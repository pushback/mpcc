#!/usr/bin/env python
# -*- coding:utf-8 -*-

__author__ = "JhonSmith(@push_back)"
__version__ = "1.0.0"

import platform
import subprocess
import re
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse

ROOT_PATH = '/'
FIND_DIR = 'find \'{}\' -maxdepth 1 -mindepth 1 -type d | sort -n'
FIND_FILE = 'find \'{}\' -maxdepth 1 -mindepth 1 -type f | grep .mp3$ | sort -n'

# switch for windows(require Git on windows)
if platform.system() == 'Windows':
    FIND_DIR = '"C:\\Program Files\\Git\\usr\\bin\\find.exe" \'{}\' -maxdepth 1 -mindepth 1 -type d'
    FIND_FILE = '"C:\\Program Files\\Git\\usr\\bin\\find.exe" \'{}\' -maxdepth 1 -mindepth 1 -type f'


class mpccGetHandler(BaseHTTPRequestHandler):
    """
    mpcc server REST API:
    /                same to "view/"
    /view/path       show dir list of path
    /exec/command    run command as `mpc command`
    """

    def do_GET(self):
        # execute command and return stdout
        def exec_cmd(command):
            print("exec_cmd : " + command)
            ret = subprocess.check_output(command)
            return ret.decode("utf-8")
        # return dir list of path

        def get_dir_list(path):
            return [p + "/" for p in exec_cmd(FIND_DIR.format(path)).split("\n") if p != '']

        # return file(*.mp3) list of path
        def get_file_list(path):
            return [p for p in exec_cmd(FIND_FILE.format(path)).split("\n") if p != '']

        try:
            req_path = self.path
            response_code = 200
            response_body = "<head><title>mpcc(mpc Client)</title></head>"
            response_body += "<body>"
            response_body += "<a href=\"{}\">Play/Stop</a> / ".format(
                urllib.parse.quote("mpc toggle"))
            response_body += 'Vol.<input type="range" list="tickmarks" value="25" min="0" max="100" onchange="document.createElement(\'img\').src=\'/exec/mpc volume \' + this.value">'
            response_body += '<datalist id="tickmarks"><option value="0"><option value="10"><option value="20"><option value="30"><option value="40"><option value="50"><option value="60"><option value="70"><option value="80"><option value="90"><option value="100"></datalist>'
            response_body += "----------"
            response_body += "<a href=\"{}\">Play Queue Init</a> / ".format(
                urllib.parse.quote("/exec/mpc clear && mpc add /", safe=''))
            response_body += "<a href=\"{}\">DB Update</a><hr>".format(
                urllib.parse.quote("/exec/mpc update --wait"))

            # / to view/
            if req_path == "" or req_path == "/":
                req_path = "/view/"

            # parse REST API
            path_list = (req_path + "").split('/')
            rest_cmd = path_list[1]
            rest_param = urllib.parse.unquote("/".join(path_list[2:]))

            # execute REST API
            if rest_cmd == "view":
                # API:view
                rest_param = ROOT_PATH + rest_param
                dir_list = ["/../"] + get_dir_list(rest_param)
                for d in dir_list:
                    rest_req = urllib.parse.quote("/view{}".format(d))
                    response_body += "<a href=\"{}\">{}</a><br>\n".format(
                        rest_req, d[1:])
                file_list = get_file_list(rest_param)
                for f in file_list:
                    rest_req = urllib.parse.quote(
                        "/exec/mpc searchplay filename '{}'".format(re.sub(r'^/mnt/', "", f)))
                    response_body += "<a href=\"{}\">{}</a><br>\n".format(
                        rest_req, f[1:])
            elif rest_cmd == "exec":
                # API:exec
                response_body = "$ {}<hr>".format(rest_param)
                response_body += exec_cmd(rest_param)
            else:
                # API:unknown
                response_code = 501
                response_body = "\"{}\" is not support API.".format(rest_cmd)

            # response return
            self.send_response(response_code)
            self.end_headers()
            self.wfile.write(response_body.encode('utf-8'))

        except Exception as e:
            # any exception throw : output error info
            self.send_response(500)
            self.end_headers()
            self.wfile.write("<body>".encode('utf-8'))
            self.wfile.write("request fail<hr>".encode('utf-8'))
            self.wfile.write(str(type(e)).encode('utf-8'))
            self.wfile.write("<br>".encode('utf-8'))
            self.wfile.write(str(e).encode('utf-8'))
            self.wfile.write("<br>".encode('utf-8'))


if __name__ == '__main__':
    print("mpcc(mpc client) server")

    # start HTTP server
    server = HTTPServer(('localhost', 80), mpccGetHandler)
    server.serve_forever()
