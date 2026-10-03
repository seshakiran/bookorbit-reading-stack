#!/usr/bin/env python3
"""Private, resumable local full-book narration with an original synthetic reference."""
import argparse, fcntl, hashlib, json, os, re, subprocess, time, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
os.environ.setdefault('HF_HOME',str(ROOT/'models'))
os.environ.setdefault('TOKENIZERS_PARALLELISM','false')
MODEL='mlx-community/Qwen3-TTS-12Hz-1.7B-Base-bf16'
CUE=ROOT/'music/chapter-cue.wav'
BEEP_PATH=None

def mastering_recipe(tempo):
    return {'tempo':tempo,'cue_sha256':hashlib.sha256(CUE.read_bytes()).hexdigest(),'cue_gap_seconds':.5,'transition_gap_seconds':1.0,'beep_sha256':hashlib.sha256(BEEP_PATH.read_bytes()).hexdigest() if BEEP_PATH else None}

def save(path,data):
    tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(data,indent=2,ensure_ascii=False));tmp.replace(path)
def run(args):
    return subprocess.run([str(x) for x in args],check=True,capture_output=True,text=True)
def duration(path):
    return float(run(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',path]).stdout)
def escape(s):
    for ch in ['\\','=',';','#']:s=s.replace(ch,'\\'+ch)
    return s.replace('\n',' ')
def master(take, tempo=1.0):
    raw=take/'raw.wav';out=take/'master.wav'
    first=run(['ffmpeg','-hide_banner','-i',raw,'-af',f'atempo={tempo},loudnorm=I=-19:TP=-2:LRA=7:print_format=json','-f','null','-'])
    measurements=json.loads(re.search(r'\{\s*"input_i".*?\}',first.stderr,re.S).group())
    filt=f'atempo={tempo},loudnorm=I=-19:TP=-2:LRA=7:linear=true:'+':'.join(f'{k}={measurements[v]}' for k,v in [('measured_I','input_i'),('measured_TP','input_tp'),('measured_LRA','input_lra'),('measured_thresh','input_thresh'),('offset','target_offset')])
    speech=take/'speech-master.wav'
    run(['ffmpeg','-v','error','-y','-i',raw,'-af',filt,'-ar','48000','-c:a','pcm_s24le',speech])
    # The cue ends before the speech. Retain the separate speech master.
    import soundfile as sf
    import numpy as np
    tmp=take/'master.partial.wav'
    with sf.SoundFile(tmp,'w',samplerate=48000,channels=1,subtype='PCM_24') as dest:
        cue,rate=sf.read(CUE,dtype='float32');assert rate==48000
        dest.write(cue);dest.write(np.zeros(24000,dtype='float32'))
        for block in sf.blocks(speech,blocksize=48000,dtype='float32'):dest.write(block)
    tmp.replace(out)
    save(take/'mastering.json',{**mastering_recipe(tempo),'target_lufs':-19,'true_peak_ceiling_db':-2,'measurements_before':measurements})
    return out

def main():
    global CUE, BEEP_PATH
    p=argparse.ArgumentParser();p.add_argument('project');p.add_argument('--duty-cycle',type=float,default=.5);p.add_argument('--limit-chapters',type=int,default=0);p.add_argument('--publish-directory');p.add_argument('--tempo',type=float,default=1.0);a=p.parse_args()
    if not 0<a.duty_cycle<=1:raise ValueError('Duty cycle must be in (0,1]')
    if not .5<=a.tempo<=2:raise ValueError('Tempo must be between 0.5 and 2')
    project=Path(a.project).resolve()
    config=json.loads((project/'production.json').read_text()) if (project/'production.json').exists() else {}
    CUE=Path(config.get('music_path',str(CUE)))
    beep_path=Path(config['beep_path']) if config.get('beep_path') else None
    BEEP_PATH=beep_path
    out=project/config.get('output_directory','warm-production');out.mkdir(exist_ok=True)
    lock=(out/'run.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    script=json.loads((project/'script.json').read_text());chapters=script['chapters'];chosen=chapters[:a.limit_chapters] if a.limit_chapters else chapters
    if config.get('require_paragraph_boundaries'):
        for chapter in chapters:
            for index,chunk in enumerate(chapter['chunks']):
                if isinstance(chunk,dict) and chunk.get('kind')=='reflection':
                    prior=chapter['chunks'][index-1] if index else {}
                    if not isinstance(prior,dict) or prior.get('kind')!='book' or not prior.get('paragraph_end'):
                        raise RuntimeError('Reflection must follow a complete source paragraph')
                    if not re.search(r'[.!?][\"\'’”]*$',prior['text'].strip()):
                        raise RuntimeError('Reflection boundary lacks a completed sentence')
    reference=Path(config.get('reference_audio',str(ROOT/'voices/warm-storyteller-reference.wav')));reftext=reference.with_suffix('.txt').read_text()
    refhash=hashlib.sha256(reference.read_bytes()).hexdigest();started=time.time();first_started=json.loads((out/'status.json').read_text()).get('first_started_at',started) if (out/'status.json').exists() else started;total=sum(len(c['chunks']) for c in chapters)
    status={'state':'loading_model','started_at':started,'first_started_at':first_started,'pid':os.getpid(),'total_chunks':total,'completed_chunks':0,'total_words':sum(c['words'] for c in chapters),'voice':'Warm Storyteller','model':MODEL,'duty_cycle':a.duty_cycle,'master_tempo':a.tempo}
    status['voice']=config.get('narrator','Warm Storyteller')
    def update(**values):status.update(values);status['updated_at']=time.time();save(out/'status.json',status)
    update()
    try:
        import mlx.core as mx
        import numpy as np
        import soundfile as sf
        from mlx_audio.tts.utils import load_model
        model=load_model(MODEL);all_entries=[];masters=[]
        for chapter in chosen:
            take=out/f'{chapter["id"]:02d}';take.mkdir(exist_ok=True);entries=[]
            for i,chunk in enumerate(chapter['chunks']):
                spec=chunk if isinstance(chunk,dict) else {'text':chunk}
                text=spec['text']
                base={'model':MODEL,'reference_sha256':refhash,'reference_text':reftext,'text':text,'seed':42000+chapter['id']*1000+i,'temperature':.8,'max_tokens':1800}
                if isinstance(chunk,dict):base['segment']=spec
                digest=hashlib.sha256(json.dumps(base,sort_keys=True).encode()).hexdigest();wav=take/f'{i+1:04d}.wav';meta=wav.with_suffix('.json')
                if meta.exists() and wav.exists():
                    entry=json.loads(meta.read_text())
                    if entry['recipe_hash']!=digest:raise RuntimeError('Recipe mismatch; preserve existing take and choose a new output directory')
                    if hashlib.sha256(wav.read_bytes()).hexdigest()!=entry['audio_sha256']:raise RuntimeError('Checkpoint audio checksum mismatch')
                else:
                    update(state='generating',chapter=chapter['title'],chapter_id=chapter['id'],chunk_in_chapter=i+1)
                    for attempt in range(3):
                        mx.random.seed(base['seed']+attempt*100000);tick=time.monotonic()
                        result=list(model.generate(text=text,ref_audio=str(reference),ref_text=reftext,lang_code='English',temperature=.8,max_tokens=1800))
                        if not result:raise RuntimeError('No audio returned')
                        rate=result[0].sample_rate;audio=np.concatenate([np.asarray(r.audio).reshape(-1) for r in result]);sec=len(audio)/rate;wpm=len(text.split())*60/max(sec,.001)
                        plausible_pace=(.4<sec<12) if len(text.split())<=8 else (75<wpm<250 and sec<140)
                        if len(audio) and np.isfinite(audio).all() and plausible_pace:break
                        print(f'Retrying implausible chunk: chapter {chapter["id"]}, chunk {i+1}, {wpm:.1f} WPM',flush=True)
                    else:raise RuntimeError('Repeated implausible output; stopped for review')
                    temp=wav.with_suffix('.part.wav');sf.write(temp,audio,rate,subtype='PCM_24');temp.replace(wav)
                    entry={**base,'recipe_hash':digest,'audio_sha256':hashlib.sha256(wav.read_bytes()).hexdigest(),'file':wav.name,'attempt':attempt+1,'seconds':sec,'generation_seconds':time.monotonic()-tick,'peak_memory_gb':mx.get_peak_memory()/1e9,'words_per_minute':wpm}
                    save(meta,entry)
                    print(f'Chapter {chapter["id"]}/{len(chapters)}, chunk {i+1}/{len(chapter["chunks"])}: {sec:.1f}s audio / {entry["generation_seconds"]:.1f}s generation; MLX peak {entry["peak_memory_gb"]:.2f} GB',flush=True)
                    mx.clear_cache()
                    idle=entry['generation_seconds']*(1/a.duty_cycle-1)
                    if idle:update(state='cooldown');time.sleep(idle)
                entries.append(entry);all_entries.append(entry)
                done_words=sum(len(e['text'].split()) for e in all_entries);gen=sum(e['generation_seconds'] for e in all_entries)
                update(completed_chunks=len(all_entries),completed_words=done_words,audio_seconds=sum(e['seconds'] for e in all_entries),active_generation_seconds=gen,peak_mlx_memory_gb=max(e['peak_memory_gb'] for e in all_entries),estimated_remaining_generation_and_idle_seconds=(status['total_words']-done_words)*gen/max(done_words,1)/a.duty_cycle)
            save(take/'manifest.json',{'chapter':chapter['title'],'model':MODEL,'chunks':entries})
            master_settings=json.loads((take/'mastering.json').read_text()) if (take/'mastering.json').exists() else {}
            if not (take/'master.wav').exists() or any(master_settings.get(k)!=v for k,v in mastering_recipe(a.tempo).items()):
                update(state='mastering_chapter')
                # Stream chunk files into a chapter WAV to bound RAM use.
                rate=sf.info(take/entries[0]['file']).samplerate
                with sf.SoundFile(take/'raw.wav','w',samplerate=rate,channels=1,subtype='PCM_24') as dest:
                    for entry_index,e in enumerate(entries):
                        if e.get('segment',{}).get('beep_before'):
                            if beep_path is None:raise RuntimeError('Missing commentary beep asset')
                            from scipy.signal import resample_poly
                            import math
                            beep,br=sf.read(beep_path,dtype='float32')
                            if br!=rate:
                                divisor=math.gcd(br,rate);beep=resample_poly(beep,rate//divisor,br//divisor)
                            dest.write(beep);dest.write(np.zeros(round(rate*.25),dtype='float32'))
                        audio,r=sf.read(take/e['file'],dtype='float32');assert r==rate
                        dest.write(audio)
                        before_reflection=entry_index+1<len(entries) and entries[entry_index+1].get('segment',{}).get('beep_before')
                        gap=1.0 if before_reflection else .35
                        dest.write(np.zeros(round(rate*gap),dtype='float32'))
                master(take,a.tempo)
            masters.append(take/'master.wav')
            if not (take/'quality-review.json').exists():
                update(state='checking_chapter')
                qa=run([config.get('qa_python',sys.executable),ROOT/'quality_check.py',take]);print(qa.stdout.strip(),flush=True)
            if config.get('require_paragraph_boundaries'):
                review=json.loads((take/'quality-review.json').read_text())
                transcripts={item['file']:item['transcript'] for item in review['chunks']}
                def ending_words(text):
                    import unicodedata
                    text=unicodedata.normalize('NFKD',text).encode('ascii','ignore').decode().lower()
                    return re.findall(r"[a-z0-9]+",text)[-3:]
                boundary_checks=[]
                for index,entry in enumerate(entries):
                    if index+1<len(entries) and entries[index+1].get('segment',{}).get('beep_before'):
                        expected=ending_words(entry['text']);heard=ending_words(transcripts[entry['file']])
                        boundary_checks.append({'file':entry['file'],'expected_ending':expected,'transcribed_ending':heard,'passed':expected==heard})
                save(take/'boundary-review.json',boundary_checks)
                if any(not item['passed'] for item in boundary_checks):
                    raise RuntimeError('A spoken ending before a beep needs review; stopping before publication')
            print(f'Chapter {chapter["id"]} master and automated transcription review ready.',flush=True)
        del model;mx.clear_cache()
        if len(chosen)<len(chapters):
            update(state='preview_ready',elapsed_seconds=time.time()-started);return
        update(state='assembling_m4b')
        concat=out/'chapters.concat';concat.write_text(''.join("file '"+str(p).replace("'","'\\''")+"'\n" for p in masters))
        metadata=[';FFMETADATA1',f'title={escape(script.get("full_title",script["title"]))}',f'artist={escape(script["author"])}',f'album={escape(script["title"])}','genre=Audiobook','comment=Private AI narration by '+config.get('narrator','Warm Storyteller')+'. Added reflections are editorial commentary, separate from the source book. Automated transcription flags require listening review.'];offset=0
        for chapter,path in zip(chapters,masters):
            end=offset+round(duration(path)*1000);metadata+=['[CHAPTER]','TIMEBASE=1/1000',f'START={offset}',f'END={end}',f'title={escape(chapter["title"])}'];offset=end
        metapath=out/'chapters.ffmeta';metapath.write_text('\n'.join(metadata)+'\n')
        final=out/config.get('output_filename','audiobook.m4b');temp=final.with_suffix('.partial.m4b')
        run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',concat,'-i',metapath,'-map_metadata','1','-map_chapters','1','-c:a','aac','-b:a','128k','-movflags','+faststart',temp])
        probe=json.loads(run(['ffprobe','-v','error','-show_chapters','-show_format','-show_streams','-of','json',temp]).stdout)
        assert len(probe['chapters'])==len(chapters)
        assert abs(float(probe['format']['duration'])-offset/1000)<1
        run(['ffmpeg','-v','error','-i',temp,'-f','null','-']);temp.replace(final);save(out/'verification.json',probe)
        published=None
        if a.publish_directory:
            import shutil
            dest=Path(a.publish_directory).resolve();dest.mkdir(parents=True,exist_ok=True);published=dest/final.name
            if published.exists():raise RuntimeError('Refusing to overwrite a previously published audiobook')
            staging=dest/(final.name+'.partial');shutil.copy2(final,staging);staging.replace(published)
        flags=sum(sum(bool(c['possible_errors']) for c in json.loads((p.parent/'quality-review.json').read_text())['chunks']) for p in masters)
        update(state='complete_needs_listening_review',elapsed_seconds=time.time()-started,total_wall_seconds_including_pause=time.time()-first_started,final_file=str(final),published_file=str(published) if published else None,final_audio_seconds=duration(final),size_bytes=final.stat().st_size,chunks_with_asr_review_flags=flags)
        print('COMPLETE:',final,flush=True)
    except BaseException as e:
        update(state='failed',error=str(e),elapsed_seconds=time.time()-started);raise
if __name__=='__main__':main()
