import fcntl
import json
import subprocess
import sys
import time
import shutil
from pathlib import Path
import tempfile
import unittest
import zipfile
from worker import prepare, read, save, status

class WorkerTests(unittest.TestCase):
    def test_extracts_spine_and_list_text_without_duplicates(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); source=root/'book.epub'
            with zipfile.ZipFile(source,'w') as z:
                z.writestr('META-INF/container.xml','<container><rootfile full-path="content.opf"/></container>')
                z.writestr('content.opf','<package xmlns="http://www.idpf.org/2007/opf"><manifest><item id="a" href="a.xhtml"/></manifest><spine><itemref idref="a"/></spine></package>')
                z.writestr('a.xhtml','<html><body><h1>Chapter One</h1><p>Hello world.</p><ul><li><p>List item.</p></li></ul><table><tr><td>Table text.</td></tr></table></body></html>')
            prepare(source,root,'Demo','Author')
            text=' '.join(read(root/'script.json')['chapters'][0]['chunks'])
            self.assertEqual(text,'Chapter One Hello world. List item. Table text.')
    def test_running_job_without_lock_becomes_interrupted(self):
        with tempfile.TemporaryDirectory() as temporary:
            job=Path(temporary)/'1-2';job.mkdir();save(job/'job.json',{'state':'running'})
            self.assertEqual(status(job,{})['state'],'interrupted')
    def test_locked_job_reports_pipeline_progress(self):
        with tempfile.TemporaryDirectory() as temporary:
            job=Path(temporary)/'1-2';job.mkdir();save(job/'job.json',{'state':'running'})
            (job/'production').mkdir();save(job/'production/status.json',{'state':'generating','completed_chunks':2,'total_chunks':8,'final_file':'private-path'})
            with (job/'active.lock').open('a') as lock:
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                result=status(job,{})
                self.assertEqual(result['state'],'generating');self.assertEqual(result['completed_chunks'],2)
                self.assertNotIn('final_file',result)
    def test_background_job_exclusion_publication_and_idempotency(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            shutil.copyfile(Path(__file__).with_name('worker.py'),root/'worker.py')
            (root/'produce_book.py').write_text("import sys,time; from pathlib import Path; p=Path(sys.argv[1])/'production'; p.mkdir(exist_ok=True); time.sleep(1); (p/'audiobook.m4b').write_bytes(b'test-audio')")
            source=root/'book.epub';source.write_bytes(b'fixture')
            (root/'ref.wav').write_bytes(b'reference');(root/'music.wav').write_bytes(b'cue')
            config=root/'config.json';save(config,{'jobs_directory':str(root/'jobs'),'python':sys.executable,'reference_audio':str(root/'ref.wav'),'music_path':str(root/'music.wav')})
            job=root/'jobs/1-2';job.mkdir(parents=True)
            import hashlib
            save(job/'script.json',{'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest()})
            command=[sys.executable,str(root/'worker.py'),'start',str(config),'1-2']
            request=json.dumps({'source':str(source),'title':'Test','author':'Demo'})
            first=json.loads(subprocess.check_output(command,input=request,text=True))
            self.assertNotIn(first['state'],['failed','interrupted'])
            second=json.loads(subprocess.check_output(command,input=request,text=True))
            self.assertIn('already being created',second['error'])
            deadline=time.monotonic()+8
            while time.monotonic()<deadline and read(job/'job.json').get('state')=='running': time.sleep(.1)
            self.assertEqual(read(job/'job.json')['state'],'complete')
            self.assertEqual(source.with_suffix('.m4b').read_bytes(),b'test-audio')
            third=json.loads(subprocess.check_output(command,input=request,text=True))
            self.assertEqual(third['state'],'complete')

    def test_missing_assets_disable_creation(self):
        with tempfile.TemporaryDirectory() as temporary:
            self.assertFalse(status(Path(temporary),{})['configured'])

if __name__=='__main__': unittest.main()
