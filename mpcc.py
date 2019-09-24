#!/usr/bin/env python3
# -*- coding:utf-8 -*-

__author__ = "JhonSmith(@push_back)"
__version__ = "1.0.0"

import os
import pathlib
import platform
import re
import subprocess
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

ROOT_PATH = '/media/sd/music/'
SKIP_PATH_REGEXP = r'^/media/sd/'

# switch for windows(require Git on windows)
if platform.system() == 'Windows':
    ROOT_PATH = '/'
    FIND_DIR = '"C:\\Program Files\\Git\\usr\\bin\\find.exe" \'{}\' -maxdepth 1 -mindepth 1 -type d'
    FIND_FILE = '"C:\\Program Files\\Git\\usr\\bin\\find.exe" \'{}\' -maxdepth 1 -mindepth 1 -type f'

# execute command and return stdout


def exec_cmd(command):
    print("exec_cmd : " + command)
    ret = subprocess.check_output(command, shell=True)
    return ret.decode("utf-8")


class mpccGetHandler(BaseHTTPRequestHandler):
    """
    mpcc server REST API:
    /                same to "view/"
    /view/path       show dir list of path
    /exec/command    run command as `mpc command`
    /playing         show dir playing file
    """

    def do_GET(self):
        # return dir list of path
        def get_dir_list(path):
            dir_list = [
                x.as_posix() + "/" for x in pathlib.Path(path).iterdir() if x.is_dir()]
            if 1 < len(dir_list):
                dir_list.sort(key=lambda x: re.sub(
                    "([0-9]+)(.+)", lambda m: ("0000" + m.group(1))[-4:] + m.group(2), x))
            return dir_list

        # return file(*.mp3) list of path
        def get_file_list(path):
            file_list = [x.as_posix() for x in pathlib.Path(
                path).glob("*.mp3") if x.is_file()]
            if 1 < len(file_list):
                file_list.sort(key=lambda x: re.sub(
                    "([0-9]+)(.+)", lambda m: ("0000" + m.group(1))[-4:] + m.group(2), x))
            return file_list

        try:
            req_path = self.path
            response_code = 200
            response_body = '''
            <head>
                <title>mpcc(mpc Client)</title>
                <style type="text/css">
                *{
                    font-size:4vw;
                }
                input{
                    min-width:3em;
                }
                p{
                    margin : 0.5em;
                }
                pre{
                    background-color:black;
                    border:1px black solid;
                    color:lightgray;
                    font-size:3vw;
                    padding:0.2em;
                    margin:5px;
                    white-space: pre-wrap;
                }
                .button:link, .button:visited, .button:hover, .button:active{
                    color: black;
                }
                .dir, .file{
                    display:block;
                    text-align:left;
                    padding:0.2em;
                    width:100%;
                }
                </style>
            </head>
            <body>'''
            response_body += "<pre>{}</pre>".format(
                exec_cmd('mpc'))
            response_body += "<p>"
            response_body += '''<input type="button" value="&lt;&lt;" onclick="document.createElement('img').src='/exec/mpc prev';location.reload()">'''
            response_body += '''<input type="button" value="|&gt;" onclick="document.createElement('img').src='/exec/mpc toggle';location.reload()">'''
            response_body += '''<input type="button" value="&gt;&gt;" onclick="document.createElement('img').src='/exec/mpc next';location.reload()">'''
            response_body += '''<input type="button" value="Vol-" onclick="document.createElement('img').src='/exec/mpc volume -1';location.reload()">'''
            response_body += '''<input type="button" value="Vol+" onclick="document.createElement('img').src='/exec/mpc volume +2';location.reload()">'''
            response_body += "</p>"
            response_body += "<p>"
            response_body += "<input type=\"button\" value=\"Playing dir\" onclick=\"location.href='/playing/'\">"
            response_body += "<input type=\"button\" value=\"Queue Init\" onclick=\"location.href='/exec/{}'\">".format(
                urllib.parse.quote("mpc clear && mpc add /", safe=''))
            response_body += "<input type=\"button\" value=\"DB Update\" onclick=\"location.href='/exec/{}'\"><hr>".format(
                urllib.parse.quote("mpc update --wait"))
            response_body += "</p>"

            # / to view/
            if req_path == "" or req_path == "/":
                req_path = "/view/"

            # parse REST API
            path_list = (req_path + "").split('/')
            rest_cmd = path_list[1]
            rest_param = urllib.parse.unquote("/".join(path_list[2:]))

            # execute REST API
            if rest_cmd == "playing":
                # API:playing
                rest_cmd = "view"
                rest_param = os.path.dirname(
                    exec_cmd("mpc -f %file%").split("\n")[0]) + "/"

            if rest_cmd == "view":
                # API:view
                response_body += "<b>{}</b>".format(rest_param)
                rest_param = ROOT_PATH + rest_param

                # dir list output
                dir_list = [rest_param + "../"] + get_dir_list(rest_param)
                for d in dir_list:
                    d = d.replace(ROOT_PATH, "", 1)
                    rest_next_param = urllib.parse.quote("{}".format(d))
                    dir_name = os.path.basename(os.path.dirname(d))
                    response_body += "<input type=\"button\" value=\"{}\" onclick=\"location.href='/view/{}'\" class=\"dir\">\n".format(
                        dir_name, rest_next_param)

                # file list output
                file_list = get_file_list(rest_param)
                for f in file_list:
                    f = f.replace(ROOT_PATH, "", 1)
                    rest_next_param = urllib.parse.quote(
                        # .format(re.sub(SKIP_PATH_REGEXP, "", f)))
                        "mpc searchplay filename '{}'".format(f.replace("'", "'\\''")))
                    file_name = os.path.basename(f)
                    response_body += "<input type=\"button\" value=\"{}\" onclick=\"document.createElement('img').src='/exec/{}'\" class=\"file\">\n".format(
                        file_name, rest_next_param)
            elif rest_cmd == "exec":
                # API:exec
                response_body += "<pre>"
                response_body += "$ {}\n".format(rest_param)
                response_body += exec_cmd(rest_param)
                response_body += "</pre>"
            elif rest_cmd == "favicon.ico":
                # 404 for "/favicon.ico" request
                response_code = 404
                response_body = "".format()
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


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""


if __name__ == '__main__':
    print("mpcc(mpc client) server")

    # get local ip addr
    # ip_addr = exec_cmd("ifconfig wlan0 | awk '/inet / {print $2}'")
    # print("ip_addr:" + ip_addr)

    # start HTTP server
    server = ThreadedHTTPServer(('', 80), mpccGetHandler)
    server.serve_forever()
