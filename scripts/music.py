"""Original backing-track generator. No samples, no copyright risk.
Usage: python3 scripts/music.py OUT.wav --seed 7 --bpm 92 --key 4 --mood warm --dur 34
"""
import numpy as np, wave, sys
def make(fn,bpm,chords,roots,dur=40,seed=0,bright=1.0):
    rng=np.random.default_rng(seed); sr=48000; beat=60/bpm
    N=int(sr*dur); t=np.arange(N)/sr; out=np.zeros((N,2))
    def note(f,start,length,amp,kind):
        s=int(start*sr); n=min(int(length*sr),N-s)
        if n<=0: return
        tt=np.arange(n)/sr
        if kind=='pad':
            w=sum(np.sin(2*np.pi*f*d*tt+ph) for d,ph in [(1,0),(1.003,1),(0.997,2),(2,0.5)])/4
            env=np.minimum(1,tt/0.8)*np.minimum(1,(length-tt)/0.8)
        elif kind=='bass':
            w=np.sin(2*np.pi*f*tt)+0.3*np.sin(2*np.pi*2*f*tt); env=np.exp(-tt*3)*np.minimum(1,tt/0.01)
        else:
            w=np.sin(2*np.pi*f*tt)*0.7+0.3*np.sin(2*np.pi*3*f*tt)*np.exp(-tt*8); env=np.exp(-tt*4)*np.minimum(1,tt/0.005)
        out[s:s+n,0]+=w*env*amp; out[s:s+n,1]+=w*env*amp
    bar=4*beat; t0=0; k=0
    while t0<dur:
        ch=chords[k%len(chords)]; r=roots[k%len(roots)]
        for f in ch: note(f,t0,bar+0.3,0.10,'pad')
        if t0>=2:
            for b in range(4): note(r/2,t0+b*beat,beat*0.9,0.33,'bass')
        if t0>=bar*2:
            seq=ch+[ch[1]*2]
            for i in range(8): note(seq[(i*3+k)%4]*2*bright,t0+i*beat/2,beat/2,0.05,'pluck')
        t0+=bar; k+=1
    tb=0.0
    while tb<dur:
        s=int(tb*sr); n=min(int(0.35*sr),N-s)
        if tb>=2 and n>0:
            tt=np.arange(n)/sr; f=50+90*np.exp(-tt*30); out[s:s+n]+=(np.sin(2*np.pi*np.cumsum(f)/sr)*np.exp(-tt*9)*0.55)[:,None]
        s2=int((tb+beat/2)*sr); n2=min(int(0.05*sr),N-s2)
        if tb>=bar and n2>0:
            w=rng.standard_normal(n2)*np.exp(-np.arange(n2)/sr*90)*0.18; w=np.diff(np.concatenate([[0],w])); out[s2:s2+n2,0]+=w*0.8; out[s2:s2+n2,1]+=w
        tb+=beat
    out*=(np.minimum(1,t/1.0)*np.minimum(1,(dur-t)/1.5))[:,None]; out/=np.max(np.abs(out))*1.12
    w=wave.open(fn,'wb');w.setnchannels(2);w.setsampwidth(2);w.setframerate(sr);w.writeframes((out*32767).astype('<i2').tobytes());w.close()

import argparse
def tri(r,minor=False):
    return [r, r*2**((3 if minor else 4)/12), r*2**(7/12)]
PROGS={'warm':[(0,0),(9,1),(5,0),(7,0)],'calm':[(0,0),(7,0),(9,1),(5,0)],'moody':[(0,1),(8,0),(3,0),(10,0)],'lift':[(0,0),(5,0),(0,0),(7,0)],'minor':[(0,1),(5,1),(10,0),(3,0)],'drive':[(0,1),(10,0),(8,0),(7,0)]}
if __name__=='__main__':
    a=argparse.ArgumentParser(); a.add_argument('out'); a.add_argument('--seed',type=int,default=1)
    a.add_argument('--bpm',type=int,default=92); a.add_argument('--key',type=int,default=0,help='semitones above C4')
    a.add_argument('--mood',default='warm',choices=list(PROGS)); a.add_argument('--dur',type=float,default=34)
    a.add_argument('--bright',type=float,default=1.0); o=a.parse_args()
    root=261.63*2**(o.key/12)
    ch=[tri(root*2**(s/12)/(2 if root*2**(s/12)>400 else 1),m) for s,m in PROGS[o.mood]]
    make(o.out,o.bpm,ch,[c[0]/2 for c in ch],dur=o.dur,seed=o.seed,bright=o.bright)
    print('wrote',o.out)
