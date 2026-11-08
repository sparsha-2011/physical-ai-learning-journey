"""Local preview server with byte-range support for browser video seeking."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import argparse
import re

ROOT=Path(__file__).resolve().parents[1]

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):
        self.byte_range=None
        super().__init__(*args,directory=str(ROOT/'web'),**kwargs)

    def send_head(self):
        self.byte_range=None
        path=Path(self.translate_path(self.path))
        requested=self.headers.get('Range')
        compressed=path.with_name(path.name+'.gz')
        if not requested and path.suffix=='.bin' and compressed.is_file() and 'gzip' in self.headers.get('Accept-Encoding',''):
            self.send_response(200)
            self.send_header('Content-Type','application/octet-stream')
            self.send_header('Content-Encoding','gzip')
            self.send_header('Vary','Accept-Encoding')
            self.send_header('Content-Length',str(compressed.stat().st_size))
            self.end_headers()
            return compressed.open('rb')
        if requested and path.is_file():
            size=path.stat().st_size
            match=re.fullmatch(r'bytes=(\d*)-(\d*)',requested)
            if not match:
                self.send_error(416);return None
            first,last=match.groups()
            start=int(first) if first else max(0,size-int(last))
            end=min(int(last),size-1) if first and last else size-1
            if start>end or start>=size:
                self.send_response(416);self.send_header('Content-Range',f'bytes */{size}');self.end_headers();return None
            f=path.open('rb');f.seek(start);self.byte_range=(start,end)
            self.send_response(206)
            self.send_header('Content-Type',self.guess_type(str(path)))
            self.send_header('Content-Length',str(end-start+1))
            self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
            self.send_header('Accept-Ranges','bytes')
            self.end_headers()
            return f
        return super().send_head()

    def end_headers(self):
        self.send_header('Accept-Ranges','bytes')
        self.send_header('Cache-Control','no-cache')
        super().end_headers()

    def copyfile(self,source,outputfile):
        if self.byte_range is None:
            return super().copyfile(source,outputfile)
        remaining=self.byte_range[1]-self.byte_range[0]+1
        while remaining:
            chunk=source.read(min(65536,remaining))
            if not chunk:break
            outputfile.write(chunk);remaining-=len(chunk)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8765);args=parser.parse_args()
    print(f'Quack Café: http://127.0.0.1:{args.port}',flush=True)
    ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()
