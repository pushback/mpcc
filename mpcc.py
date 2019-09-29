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
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from time import mktime
from wsgiref.handlers import format_date_time

from mutagen.mp3 import MP3

ROOT_PATH = '/media/music/'
SKIP_PATH_REGEXP = r'^/media/'

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
    /cover/path      return coverart jpg or png
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
            response_mode = 'text'
            response_code = 200
            response_header = []
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
                .cover{
                    background-color:black;
                    color:lightgray;
                    float:left;
                    height:256px;
                    margin:0.2em;
                    width:256px;
                }
                .music-status{
                    background-color:black;
                    float:left;
                    margin:5px;
                    padding:0px;
                    width:100%;
                }
                .music-ctl{
                    clear:left;
                }
                </style>
            </head>
            <body>'''
            response_body += "<div class=\"music-status\">"
            playing_path = exec_cmd("mpc -f %file%").split("\n")[0]
            if os.path.isfile(ROOT_PATH + playing_path):
                response_body += "<img src=\"/cover/{}\" alt=\"coverart\" onerror=\"this.alt='no image'\" class=\"cover\">".format(
                    urllib.parse.quote(playing_path))
            response_body += "<pre>{}</pre>".format(
                re.sub(r' +repeat.+', '', exec_cmd('mpc')))
            response_body += "</div>"
            response_body += "<p class=\"music-ctl\">"
            response_body += '''<input type="button" value="&lt;&lt;" onclick="document.createElement('img').src='/exec/mpc prev';setTimeout('location.reload()',500)">'''
            response_body += '''<input type="button" value="|&gt;" onclick="document.createElement('img').src='/exec/mpc toggle';setTimeout('location.reload()',500)">'''
            response_body += '''<input type="button" value="&gt;&gt;" onclick="document.createElement('img').src='/exec/mpc next';setTimeout('location.reload()',500)">'''
            response_body += '''<input type="button" value="Vol-" onclick="document.createElement('img').src='/exec/mpc volume -1';setTimeout('location.reload()',500)">'''
            response_body += '''<input type="button" value="Vol+" onclick="document.createElement('img').src='/exec/mpc volume +2';setTimeout('location.reload()',500)">'''
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
                    response_body += "<input type=\"button\" value=\"{}\" onclick=\"document.createElement('img').src='/exec/{}';setTimeout('location.reload()',500)\" class=\"file\">\n".format(
                        file_name, rest_next_param)
            elif rest_cmd == "exec":
                # API:exec
                response_body += "<pre>"
                response_body += "$ {}\n".format(rest_param)
                response_body += exec_cmd(rest_param)
                response_body += "</pre>"
            elif rest_cmd == "cover":
                # API:cover
                rest_param = ROOT_PATH + rest_param

                if not os.path.isfile(rest_param):
                    response_code = 404
                    response_body = "".format()
                elif "If-Modified-Since" in self.headers:
                    # 2nd time response is Not Modified.
                    response_code = 304
                    response_body = "".format()
                else:
                    # 1st time response is coverart data.
                    response_body = "".format()
                    tags = MP3(rest_param).tags
                    # print(tags.pprint())
                    apic = tags.getall('APIC')[0]
                    # print("mime:{}, data:{}Byte".format(
                    #     apic.mime, len(apic.data)))
                    response_header.append(("Content-Type", apic.mime))
                    response_header.append(("Content-Disposition", "inline"))
                    response_header.append(
                        ("Last-Modified", format_date_time(mktime(datetime.now().timetuple()))))
                    response_mode = 'binary'
                    response_body = apic.data
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
            for header in response_header:
                self.send_header(header[0], header[1])
            self.end_headers()
            if response_mode == 'text':
                self.wfile.write(response_body.encode('utf-8'))
            else:
                self.wfile.write(response_body)

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
