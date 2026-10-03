#!/usr/bin/env python3
"""Private, single-worker audiobook jobs. Called only by the authenticated server."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import time
import zipfile
import xml.etree.ElementTree as ET
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent


def save(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2))
    temporary.replace(path)


def read(path):
    return json.loads(path.read_text()) if path.exists() else {}


def prepare(source, project, title, author):
    from bs4 import BeautifulSoup
    chapters = []
    with zipfile.ZipFile(source) as archive:
        if sum(i.file_size for i in archive.infolist()) > 256 * 1024 * 1024:
            raise ValueError('EPUB expanded size exceeds 256 MB')
        container = ET.fromstring(archive.read('META-INF/container.xml'))
        opf = next(e.attrib['full-path'] for e in container.iter() if e.tag.endswith('rootfile'))
        package = ET.fromstring(archive.read(opf))
        items = {e.attrib['id']: e.attrib for e in package.iter() if e.tag.endswith('}item')}
        for element in package.iter():
            if not element.tag.endswith('}itemref') or element.attrib.get('linear') == 'no':
                continue
            item = items[element.attrib['idref']]
            if 'nav' in item.get('properties', '').split():
                continue
            href = str(PurePosixPath(opf).parent / unquote(item['href'].split('#')[0]))
            soup = BeautifulSoup(archive.read(href), 'html.parser')
            for tag in soup.select('script,style,nav'):
                tag.decompose()
            body = soup.body or soup
            # Leaf blocks preserve list/table text without duplicating nested paragraphs.
            blocks = [b for b in body.find_all(['h1', 'h2', 'h3', 'p', 'li', 'td', 'blockquote'])
                      if not b.find(['h1', 'h2', 'h3', 'p', 'li', 'td', 'blockquote'])]
            texts = [re.sub(r'\s+', ' ', b.get_text(' ', strip=True)).strip() for b in blocks]
            texts = [t for t in texts if t]
            if not texts:
                fallback = body.get_text(' ', strip=True)
                if fallback:
                    texts = [fallback]
            if not texts:
                continue
            chunks = []
            for paragraph in texts:
                words = paragraph.split()
                # Bound model inputs even when punctuation is missing.
                chunks.extend(' '.join(words[n:n+100]) for n in range(0, len(words), 100))
            heading = body.find(['h1', 'h2', 'h3'])
            chapters.append({'id': len(chapters)+1, 'title': heading.get_text(' ', strip=True) if heading else f'Section {len(chapters)+1}',
                             'chunks': chunks, 'words': sum(len(t.split()) for t in chunks), 'source': href})
    if not chapters:
        raise ValueError('No readable EPUB text found')
    save(project/'script.json', {'title': title, 'author': author, 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'chapters': chapters})


def status(job, config):
    state = read(job/'job.json')
    pipeline = read(job/'production/status.json')
    result = {'state': state.get('state', 'idle'), 'linkedBookId': state.get('linkedBookId'),
              'configured': all(Path(config.get(k, '/missing')).is_file() for k in ('python', 'reference_audio', 'music_path')),
              'narrator': config.get('narrator', 'Storyteller')}
    if state.get('state') == 'running':
        # PID reuse cannot incorrectly mark a job running: the per-job lock is authoritative.
        with (job/'active.lock').open('a') as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                result['state'] = 'interrupted'
            except BlockingIOError:
                result['state'] = pipeline.get('state', 'preparing')
    for key in ('completed_chunks', 'total_chunks', 'estimated_remaining_generation_and_idle_seconds', 'chunks_with_asr_review_flags'):
        if key in pipeline:
            result[key] = pipeline[key]
    if result['state'] == 'failed':
        result['message'] = 'Creation stopped. Check the private job log, correct the problem, then Resume.'
    if result['state'] == 'complete':
        result['message'] = 'Ready. Automated review is not a substitute for listening. Pair this edition in BookBridge for e-reader handoff.'
    return result


def execute(job, config, lock_fd, job_lock_fd):
    # The inherited descriptor holds the global lock throughout synthesis, QA and publication.
    lock = os.fdopen(lock_fd, 'a')
    job_lock = os.fdopen(job_lock_fd, 'a')
    request = read(job/'request.json')
    try:
        source = Path(request['source'])
        if not (job/'script.json').exists():
            prepare(source, job, request['title'], request['author'])
        elif read(job/'script.json')['source_sha256'] != hashlib.sha256(source.read_bytes()).hexdigest():
            raise ValueError('Source changed; refusing to reuse old narration checkpoints')
        production = {k: config[k] for k in ('reference_audio', 'music_path', 'narrator', 'qa_python') if k in config}
        production.update(output_directory='production', output_filename='audiobook.m4b')
        if (job/'production.json').exists() and read(job/'production.json') != production:
            raise ValueError('Narrator configuration changed; preserve existing checkpoints')
        save(job/'production.json', production)
        env = os.environ.copy()
        if config.get('model_cache'):
            env['HF_HOME'] = config['model_cache']
        subprocess.run([config['python'], '-u', str(ROOT/'produce_book.py'), str(job), '--tempo', '0.93', '--duty-cycle', '0.5'], check=True, env=env, pass_fds=(lock.fileno(), job_lock.fileno()))
        output = job/'production/audiobook.m4b'
        # Put generated audio next to the EPUB for watched library imports, never overwrite media.
        destination = source.with_suffix('.m4b')
        if not destination.exists():
            temporary = destination.with_suffix('.m4b.partial')
            shutil.copyfile(output, temporary)
            try:
                os.link(temporary, destination)
            finally:
                temporary.unlink(missing_ok=True)
        elif hashlib.sha256(destination.read_bytes()).digest() != hashlib.sha256(output.read_bytes()).digest():
            raise ValueError('A different audiobook already exists; refusing to replace it')
        save(job/'job.json', {'state': 'complete'})
    except BaseException:
        save(job/'job.json', {'state': 'failed'})
        raise
    finally:
        lock.close()
        job_lock.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['status', 'start', 'run', 'link', 'audio'])
    parser.add_argument('config')
    parser.add_argument('key')
    parser.add_argument('--lock-fd', type=int)
    parser.add_argument('--job-lock-fd', type=int)
    args = parser.parse_args()
    if not re.fullmatch(r'[1-9][0-9]*-[1-9][0-9]*', args.key):
        raise ValueError('Invalid job identity')
    config = read(Path(args.config))
    jobs = Path(config['jobs_directory']).resolve()
    jobs.mkdir(parents=True, exist_ok=True)
    job = jobs/args.key
    job.mkdir(exist_ok=True)
    if args.action == 'run':
        execute(job, config, args.lock_fd, args.job_lock_fd)
        return
    if args.action == 'audio':
        if read(job/'job.json').get('state') != 'complete':
            raise ValueError('Audiobook not ready')
        print(json.dumps({'path': str(job/'production/audiobook.m4b')}))
        return
    if args.action == 'link':
        request = json.load(sys.stdin)
        old = read(job/'job.json')
        old['linkedBookId'] = int(request['linkedBookId'])
        save(job/'job.json', old)
    if args.action == 'start':
        if not status(job, config)['configured']:
            print(json.dumps({'error': 'Studio is not configured'}))
            return
        lock = (jobs/'gpu.lock').open('a')
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print(json.dumps({'error': 'An audiobook is already being created. Try again after it finishes.'}))
            return
        job_lock = (job/'active.lock').open('a')
        fcntl.flock(job_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        request = json.load(sys.stdin)
        if read(job/'job.json').get('state') == 'complete':
            print(json.dumps(status(job, config)))
            return
        existing = [Path(request['source']).with_suffix(ext) for ext in ('.m4b', '.mp3', '.m4a', '.flac', '.ogg', '.opus')]
        if any(path.exists() for path in existing) and not (job/'production/audiobook.m4b').exists():
            print(json.dumps({'error': 'Audio already exists beside this EPUB. Scan the library and link its audio entry instead.'}))
            return
        save(job/'request.json', request)
        save(job/'job.json', {'state': 'running'})
        if (job/'production/status.json').exists():
            pipeline = read(job/'production/status.json')
            pipeline['state'] = 'preparing'
            save(job/'production/status.json', pipeline)
        with (job/'worker.log').open('a') as log:
            try:
                subprocess.Popen([config['python'], str(Path(__file__).resolve()), 'run', args.config, args.key, '--lock-fd', str(lock.fileno()), '--job-lock-fd', str(job_lock.fileno())],
                                 stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True, pass_fds=(lock.fileno(), job_lock.fileno()))
            except OSError:
                save(job/'job.json', {'state': 'failed'})
                raise
    print(json.dumps(status(job, config)))


if __name__ == '__main__':
    main()
