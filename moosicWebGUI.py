#!/usr/bin/env python
# -*- coding: Latin-1 -*-
#:tabSize=4:indentSize=4:noTabs=true:mode=python:encoding=ISO-8859-1:
#
########################################################################
#
#   moosicWebGUI -- web GUI for controlling the moosicd daemon
#
#   Copyright (C) 2004, 2005 Eckhard Licher, Frankfurt, Germany.
#
#   This program is free software; you can redistribute it
#   and/or modify it under the terms of version 2 of the GNU
#   General Public License as published by the Free Software
#   Foundation.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License (contained in file COPYING) for more
#   details.
#
########################################################################

"""
moosicWebGUI(1)
=============
Eckhard Licher <develf@online.de>
v0.9, Dec03 2005


NAME
----
moosicWebGUI - web GUI for controlling the moosicd daemon


SYNOPSIS
--------
'moosicWebGUI.py' [-p number] [-s] [-i] [-j name] [-a host]
[-n net] [-h] [-m] [-d] [-c configdir] [-t template]
[--port=number] [--server-only] [--ignore-exit]
[--jukebox-dir=name] [--add-host=host] [--add-network=net]
[--help] [--manual] [--debug] [--config=configdir]
[--template=template]


DESCRIPTION
-----------
'moosicWebGUI' is a web GUI based on a simple HTTP server with
special built-in commands for controlling the moosicd daemon.
The HTTP server implementation only handles GET and HEAD
requests. POST requests are not implemented.


OPTIONS
-------
'-p number, --port=number'::
        set the server's portnumber to number

'-s, --server-only'::
        server-only mode, no browser is launched

'-i', '--ignore-exit'::
        ignore exit request via HTTP request

'-j, --jukebox-dir'::
        select directory containing music files

'-a, --add-host'::
        add host to list of allowed hosts (ip address or host name)

'-n, --add-network'::
        add network to list of allowed networks;
        network is specified with CIDR notation, e.g. 192.168.0.0/24

'-h, --help'::
        display help message and exit

'-m, --manual'::
        display this manual page and exit

'-d, --debug'::
        include debug information in HTML pages

'-c configdir, --config=configdir'::
        take moosic configuration from configdir

'-t template, --template=template'::
        use specified template file

Options specified at the command line are evaluated from left
to right.

When invoked without options, 'moosicWebGUI' serves HTTP
requests through port 8000.  In case port 8000 is already in
use the server searches for an unused port by subsequently
incrementing the port number and trying to bind to the port
unless option '-p' is specified. If option '-p' is specified
the port auto-search function is turned off.

Unless option '-s' is specified 'moosicWebGUI' tries to
launch the system's web browser with the initial URL pointing
to the internal web server.

'moosicWebGUI' can be terminated with a HTTP request to '/exit'.
This exit request can be disabled with option '-i'.

The directory containing music files is assumed to be $HOME.
In case $HOME is not set /tmp is assumed to be the jukebox
directory. It may be explicitly specified by option '-j'.

For security reasons only requests originating from the local
machine are being served by default. Other hosts need to be
included explicitly to the access control list by means of
option '-a'. Option '-a' may be used more than once in order
to allow access from several hosts.  Additionally, entire
networks may be specified using option '-n'; network addresses
shall be specified using CIDR format (e.g. 192.168.0.0/24).

Incorrect invocation of the program as well as option '-h'
display a brief help message. The full manual page, i.e. this
document, is printed through option '-m'. In either case
program execution terminates regardless of other options
possibly specified.

If option '-d' is specified some debug information and a link
to the wdg's html validator is included in the generated HTML
pages. To validate pages package wdg-html-validator needs to
be installed.

The moosic configuration is read from the default directory
($HOME/.moosic/ or /tmp/.moosic/) unless option '-c' is
specified.

An alternate template may be specified by means of option '-t'.


FILES
-----
template.html::
    Page template file used for content generation.

COPYING::
    License text (GPL version 2).


ENVIRONMENT
-----------
HOME::
    The user's home directory is taken as the default jukebox
    directory. Overridden by the -j option.


DIAGNOSTICS
-----------
The following diagnostics may be issued on stderr:

DNS lookup for host <host> failed.::
    The host's IP address could not be resolved -- check spelling.

<network> is not a valid network specification.::
    The network specification is not valid -- it shall be in CIDR
    format, e.g. 192.168.0.0/24.

The moosicd server doesn't seem to be running, and it could not ...::
    For some reason it was not possible to start the moosicd server.

An attempt was made to start the moosic server, but ...::
    An attempt was made to start the moosic server, but for some strange
    reason it was not possible to start the moosicd server.

Moosic api version <version> is not supported (must be 1.7 or later).::
    Use a moosic version >= 1.5.

Can not connect to port <port>::
    The webserver could not connect to port <port> -- use a free port
    higher than port number 1024.

Can not start new server, giving up. Sorry.::
    The webserver terminated due to a weird error and could not
    be restarted.


AVAILABILITY
------------
'moosicWebGUI' is available on all platforms supporting Python 2.2
or later.


CAVEATS
-------
This is alpha software, so beware.

The jukebox directory may any directory other than '/'. This should
be considered to be a feature :-)


BUGS
----
Please send bug reports to the author.


AUTHOR
------
2005 Eckhard Licher, Frankfurt, Germany. <develf at online dot de>


ACKNOWLEDGEMENTS
----------------
The code for the initiation of the connection to moosicd and the
easter egg was adapted from the moosic client written by Daniel
Pearson <daniel at nanoo dot org>.

Options -n, -c and -t: the code for access control list for entire
networks, scanning of moosic config file for supported file types
and the use of alternate template file (introduced in version 0.8.1)
was contributed by Forest Bond <forest at alittletooquiet dot net>.


SEE ALSO
--------
moosic(1), moosicd(1), validate(1)
"""

#######################################################################
# NOTE
#######################################################################
# The text contained in the preceding docstring contains the program's
# man page in asciidoc format. The asciidoc source can be converted to
# HTML and/or docbook-sgml (for docbook2man post-processing).
#
# Extract the docstring with the following command and post-process
# with asciidoc (and possibly docbook2man) as desired:
# $ python moosicWebGUI.py -m > moosicWebGUI.asc
#######################################################################


# Import needed python modules

import getopt, os, os.path, socket, string, sys, time
import urllib, errno, random, re, fileinput, base64, marshal
import BaseHTTPServer, SimpleHTTPServer, webbrowser
import moosic.client.factory
from xmlrpclib import Binary

# Request Handler for HTTP requests to our server

class moosicWebGUIHTTPRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    """
    Complete HTTP server with GET and HEAD commands.
    GET and HEAD support for special moosicWebGUI built-in functions.
    The POST command is not implemented.
    """

    def do_HEAD(self):
        """send headers"""
        if not allowed_to_connect(self.client_address[0]):
            self.send_response(403)
        else:
            self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_GET(self):
        """Execute a moosicWebGUI function"""

        # make sure we are connected from an allowed host
        if not allowed_to_connect(self.client_address[0]):
            self.send_response(403, 'Forbidden')
            self.wfile.write('Content-type: text/html\n\n')
            self.wfile.write('''
                <h1>Forbidden</h1><p>Access denied. Your host is neither
                included in ACL 'allowed_hosts' nor in ACL 'allowed_networks'.</p>
                ''')
            return

        self.message     = ""
        self.dyn_content = ''
        form             = {}

        # favicon.ico requested ?
        if self.path == "/favicon.ico":
            self.send_response(200, 'OK')
            self.wfile.write('Content-type: image/x-ms-bmp\n\n')
            try:
                image = open(os.path.join(mydir, "favicon.ico"),"rb").read()
                self.wfile.write(image)
            except IOError:
                pass
            return

        # favicon.ico requested ?
        if self.path.endswith(".html"):
            print mydir
            print self.path
            fname = os.path.join(mydir, self.path[1:])
            try:
                text = open(fname,"rb").read()
                self.send_response(200, 'OK')
                self.wfile.write('Content-type: text/html\n\n')
                self.wfile.write(text)
            except IOError:
                self.send_response(404, 'not found')
                self.wfile.write('Content-type: text/html\n\n')
                self.wfile.write("<h1>file '%s' not found</h1>" % fname)
            return

        # extract information from request
        command = self.path[1:]    # we don't need the initial '/'
        pos = string.find(command,"?")
        if pos > -1:
            # strip off additional request parameters and store in 'form' variable
            params = command[pos+1:]
            command=command[:pos]
            # extract additional request parameters
            parlist = string.split(params,"&")
            for par in parlist:
                chunks = string.split(par,"=")
                if len(chunks)>1:
                    form[urllib.unquote_plus(chunks[0])] = urllib.unquote_plus(chunks[1])
                else:
                    form[urllib.unquote_plus(chunks[0])] = None

        # check existance and/or validity parameters supplied with request:
        if not command:
            command = "index"
        # view type
        self.view = form.get("view", "")
        if self.view not in ("history", "playlist", "files", "tree", "search"):
            self.view = "standard"
        # search pattern
        self.pattern = form.get("pattern", "")
        # load mode for stored playlists
        self.lmode = form.get("lmode", "append")
        # "current working directory"
        self.mypath = form.get("path", myroot)
        if string.find(self.mypath, myroot) != 0 or string.find(self.mypath,"/..") >= 0:
            self.mypath = myroot
        # directory argument (files to append, mixin...)
        self.dir = form.get("dir", "")
        if string.find(self.dir, myroot) != 0 or string.find(self.dir,"/..") >= 0:
            self.dir = myroot
        # filename argument
        self.file = form.get("file", "")
        if string.find(self.file, myroot) != 0 or string.find(self.file,"/..") >= 0:
            self.file = myroot
        # number argument (for skip etc.)
        self.count = 0
        if form.has_key("count"):
            try:
                self.count = int(form["count"])
            except ValueError:
                pass
        # position in playlist
        self.pos = 0
        if form.has_key("pos"):
            try:
                self.pos = int(form["pos"])
            except ValueError:
                pass

        # get current moosicd status
        self.is_queue_running = proxy.is_queue_running()
        self.is_looping       = proxy.is_looping()
        self.is_paused        = proxy.is_paused()
        self.queue_length     = proxy.queue_length()

        #####################
        # command dispatcher.
        #####################
        if hasattr(self, "_do__" + command):
            # execute functions which return special pages -- processing ends here
            if debug:
                print "executing _do__" + command
            meth = getattr(self, "_do__" + command)
            meth()
            return
        elif hasattr(self, "_do_" + command):
            # execute functions which return standard pages
            if debug:
                print "executing _do_" + command
            meth = getattr(self, "_do_" + command)
            meth()
        else:
            self.message += '<font color="#aa0000">Command "%s" is not (yet) implemented. </font>' % command

        # if the function called by the dispatcher did not produce a message
        # we just say which function was executed
        if not self.message:
            self.message += "Command '%s' executed. " % command

        # moosicd has some latency time for some commands, so we just wait a bit
        time.sleep(0.05)

        # if the function called by the dispatcher did not produce its own content
        # we create content for the selected view type
        if not self.dyn_content:
            meth = getattr(self, "cont_" + self.view)
            self.dyn_content = meth()

        # get current moosicd status (again)
        is_queue_running = proxy.is_queue_running()
        is_looping       = proxy.is_looping()
        is_paused        = proxy.is_paused()
        queue_length     = proxy.queue_length()
        time.sleep(0.05)
        current_track    = proxy.current().data
        current_time     = proxy.current_time()

        # write headers
        self.send_response(200, 'Script output follows')
        self.wfile.write('Content-type: text/html\n\n')

        # build result page from template
        content = template
        if debug:
            content = string.replace(content, "@@debug", "<hr><pre>\n%s\n%s</pre><hr>" % (self.path,form))
        else:
            content = string.replace(content, "@@debug", "")

        if is_looping:
            txt = "<b>looping</b>"
            content = string.replace(content, "@@P1@@", "phigh")
            if current_track:
                content = string.replace(content, '@@del_current', '<a href="del_current?@@params"><i>remove</i></a>')
            else:
                content = string.replace(content, "@@del_current", " ")
        else:
            txt = "not looping"
            content = string.replace(content, "@@P1@@", "pnorm")
            content = string.replace(content, "@@del_current", " ")
        content = string.replace(content, "@@looping", '<a href="loop?@@params">%s</a>' % txt)

        if is_queue_running:
            txt = "advancing"
            content = string.replace(content, "@@P2@@", "pnorm")
        else:
            txt= "<b>not advancing</b>"
            content = string.replace(content, "@@P2@@", "phigh")
        content = string.replace(content, "@@advancing", '<a href="advance?@@params">%s</a>' % txt)

        if is_paused:
            txt = "<b>pause</b>"
            content = string.replace(content, "@@P3@@", "phigh")
        else:
            txt = "not paused"
            content = string.replace(content, "@@P3@@", "pnorm")
        content = string.replace(content, "@@pause", '<a href="pause?@@params">%s</a>' % txt)

        content = string.replace(content, "@@message", "%s" % self.message)
        content = string.replace(content, "@@time", "%s" % current_time)
        content = string.replace(content, "@@current_track", format_name(current_track))
        content = string.replace(content, "@@remaining", "<b>%d</b> remaining" % queue_length)
        if ignore_exit:
            content = string.replace(content, "@@exit", '')
        else:
            content = string.replace(content, "@@exit", '<a href="exit?@@params">exit moosicWebGUI</a>')
        if debug:
            url = "http://localhost:%d%s" % (port, self.path)
            url = string.replace(url, "&", "&amp;")
            url = "?url=" + url + "&amp;input=yes&amp;warnings=yes"
            url = "http://localhost/cgi-bin/validate.cgi" + url
            content = string.replace(content, "@@validate", \
               '<a target="val" href="%s">validate page</a>' % url)
        else:
            content = string.replace(content, "@@validate", "")
        content = string.replace(content, "@@content", "%s" % self.dyn_content)
        # @@params shall be last (@@content and @@exeit use @@params)
        content = string.replace(content, "@@cform", clear_form % \
                    (self.view, self.mypath))
        content = string.replace(content, "@@sform", search_form % \
                    ("search", "search", self.mypath, self.pattern, "search music files"))
        content = string.replace(content, "@@params", 'path=%s&amp;view=%s&amp;pattern=%s' % \
                    (urllib.quote(self.mypath), urllib.quote(self.view),
                     urllib.quote(self.pattern)))
        # write page
        self.wfile.write(content)

    #-------------------------------------------

    def _do__list2(self):
        """write current state of playlist to text file/plain page in .m3u format"""
        playlist = [i.data for i in proxy.list()]
        self.send_response(200, 'Script output follows')
        self.wfile.write('Content-type: text/plain\n\n')
        self.wfile.write('#EXTM3U\n')
        for item in playlist:
            pos1 = string.rfind(item, '/')
            pos2 = string.rfind(item, '.')
            self.wfile.write('#EXTINF:-1,%s\n' % item[pos1+1:pos2].replace('_',' '))
            self.wfile.write('%s\n' % item)

    #-------------------------------------------

    def _do_add_bottom(self):
        """add all files from directory tree to bottom of playlist"""
        if self.dir:
            dir = self.dir
            #files = os.popen('find "%s" -type f -print' % dir).readlines()
            files = getfiles(dir)
            files.sort()
            count = 0
            proxy.halt_queue()
            for file in files:
                if file_is_moosical(file) and string.find(file, "/.") < 0:
                    proxy.append([Binary(file)])
                    count += 1
            if self.is_queue_running:
                proxy.run_queue()
            self.message += "%d files added to bottom of playlist from directory '%s'. " % (count, dir[len(myroot)+1:])
        else:
            self.message += "Weird error -- no directory name given. "

    def _do_add_top(self):
        """add all files from directory tree to top of playlist"""
        if self.dir:
            dir = self.dir
            files = getfiles(dir)
            files.sort()
            files.reverse()
            count = 0
            proxy.halt_queue()
            for file in files:
                if file_is_moosical(file) and string.find(file, "/.") < 0:
                    proxy.prepend([Binary(file)])
                    count += 1
            if self.is_queue_running:
                proxy.run_queue()
            self.message += "%d files added to top of playlist from directory '%s'. " % (count, dir[len(myroot)+1:])
        else:
            self.message += "Weird error -- no directory name given. "

    def _do_advance(self):
        """toggle advance mode"""
        if self.is_queue_running:
            proxy.halt_queue()
        else:
            proxy.run_queue()

    def _do_append(self):
        """add single file to bottom of playlist"""
        proxy.append([Binary(self.file)])
        self.message += "File '%s' appended to playlist. " % format_name(self.file)

    def _do_chdir(self):
        """change current working directory"""
        try:
            if self.dir != myroot and os.path.islink(self.dir):
                self.message += "For security reasons I will not follow symlinks. "
            else:
                entries = os.listdir(self.dir)
                self.mypath = self.dir
        except OSError:
            self.message += "You do not have permission to access directory '%s'. " % (self.dir[len(myroot)+1:])
        self.view = "files"

    def _do_clear(self):
        """prepare confirmation page for clear playlist command"""
        self.message += " "
        self.dyn_content += '''<p>&nbsp;</p>
                               <p>Click <a href="clear2?@@params"><strong>here</strong></a> to confirm:
                               clear (remove all items from) playlist. </p>
                               <p>&nbsp;</p>
                               '''

    def _do_clear2(self):
        """clear playlist"""
        proxy.clear()

    def _do_clearmemo(self):
        """prepare confirmation page for clear memo command"""
        self.message += " "
        self.dyn_content += '''<p>&nbsp;</p>
                               <p>Click <a href="clearmemo2?@@params"><strong>here</strong></a> to confirm:
                               clear MEMO (playlist '%s'). </p>
                               <p>&nbsp;</p>
                               ''' % memo_file

    def _do_clearmemo2(self):
        """clear memo"""
        try:
            file = open(memo_file, "w")
            file.write('#EXTM3U\n')
            file.close()
            self.message += "MEMO cleared, playlist '%s' is now empty. " % memo_file
        except IOError:
            self.message += "can not access MEMO (playlist '%s'). " % memo_file

    def _do_del_current(self):
        """stop current track, remove it from playlist and play next song, if any"""
        current_track = proxy.current().data
        if not current_track:
            self.message += "There is currently no track playing that can be removed. "
        else:
            proxy.stop()
            playlist = [i.data for i in proxy.list()]
            del playlist[0]
            proxy.replace([Binary(i) for i in playlist])
            proxy.run_queue()
            # wait a bit for moosicd...
            time.sleep(0.05)
            if self.is_paused:
                proxy.pause()

    def _do_deldup(self):
        """delete all duplicate entries in playlist"""
        oldlist = [i.data for i in proxy.list()]
        newlist = []
        temp    = {}
        for track in oldlist:
            if not temp.has_key(track):
                temp[track]=None
                newlist.append(track)
        proxy.replace([Binary(i) for i in newlist])
        self.message += "%d items deleted from playlist. " % (self.queue_length - proxy.queue_length())

    def _do_exit(self):
        """write good-bye message and exit program"""
        global end_flag, ignore_exit

        if not ignore_exit:
            self.message += 'Oh well. '
            self.dyn_content += '''
               <p>&nbsp;</p>
               <p>Click <a href="exit2"><strong>here</strong></a> to exit moosicWebGUI (moosicd will keep running).</p>
               <p>&nbsp;</p>
               '''
        else:
            self.message += 'Exit requests are ignored, moosicWebGUI still running... '

    def _do_exit2(self):
        """write good-bye message and exit program"""
        global end_flag, ignore_exit
        if not ignore_exit:
            end_flag = True
            self.dyn_content += '<br><h1>moosicWebGUI terminated (moosicd still running). Good-bye.</h1><br>'
        else:
            self.message += 'Exit requests are ignored, moosicWebGUI still running... '

    def _do_files(self):
        """switch to file view mode"""
        self.view = "files"

    def _do_history(self):
        """swtitch to history view mode"""
        self.view = "history"

    def _do_index(self):
        """initial page"""
        self.message += "Welcome to moosicWebGUI. "

    def _do_license(self):
        """display license (file COPYING)"""
        try:
            license = open(os.path.join(mydir, "COPYING"),"r").read()
            self.dyn_content += "<pre>\n" + license + "\n</pre>\n"
            self.message += "Please respect the GPL. "
        except IOError:
            self.message += 'File COPYING seems to be missing. The <a href="http://www.fsf.org/">FSF</a> certainly has a copy...\n'

    def _do_list(self):
        """display instructions for save playlist command"""
        self.dyn_content += """
                            <p>&nbsp;</p>
                            <p>Save the next screen (opens in new window) with your browser's save command
                            to a file in directory '%s' or one of its subdirectories. The filename should have
                            the extension '.m3u'.</p>
                            <p>When done you might wish to re-scan the jukebox directory so your newly created
                            playlist file shows up in the 'load playlist from file' menu.</p>
                            <p>Click <a target="moosic2" href="list2?@@params"><strong>here</strong></a>
                            to proceed. </p>
                            <p>&nbsp;</p>
                            """ % myroot
        self.message += "Please follow the instructions. "

    def _do_list_memo(self):
        """show content of MEMO playlist"""
        self.listPL(memo_file)

    def _do_list_pl(self):
        """show content of playlist"""
        self.listPL(self.file)

    def _do_load(self):
        """display stored playlists"""
        global playlists
        content = ['<table class="menu" border="0" width="100%" cellspacing="0">\n']
        content.append('<tr><th colspan="6" align="left">Stored playlists</th></tr>\n')
        count = 0
        for file in playlists:
            content.append('<tr>')
            content.append('<td class="%s">%s</td>\n' % (klass[count&1], format_name(file)))
            content.append('<td class="%s"><a href="list_pl?@@params&amp;file=%s">show content</a></td>\n' % (klass[count&1],urllib.quote(file)))
            content.append('<td class="%s"><a href="load_pl?@@params&amp;file=%s&amp;lmode=replace">replace&nbsp;PL</a></td>\n' % (klass[count&1],urllib.quote(file)))
            content.append('<td class="%s"><a href="load_pl?@@params&amp;file=%s&amp;lmode=mixin">mixin</a></td>\n' % (klass[count&1],urllib.quote(file)))
            content.append('<td class="%s"><a href="load_pl?@@params&amp;file=%s&amp;lmode=prepend">prepend</a></td>\n' % (klass[count&1],urllib.quote(file)))
            content.append('<td class="%s"><a href="load_pl?@@params&amp;file=%s&amp;lmode=append">append</a></td>' % (klass[count&1],urllib.quote(file)))
            content.append('</tr>\n')
            count += 1
        if not playlists:
            content.append('<tr><td colspan="5">(There are no stored playlists).</td></tr>\n')
        content.append("</table>\n")
        self.message += "Found %d stored playlists. " % len(playlists)
        self.dyn_content = ''.join(content)

    def _do_load_pl(self):
        """load playlist from file"""
        if self.file:
            try:
                files = open(self.file).readlines()
            except IOError:
                self.message += "Can't open playlist file '%s'. " % self.file
                return
            count = 0
            result = []
            files = [string.strip(file) for file in files]
            files = [file for file in files if file and file[:1] != '#']
            for file in files:
                if file_is_moosical(file) and string.find(file, "/.") < 0:
                    result.append(file)
                    count += 1
            playlist = [i.data for i in proxy.list()]
            if self.lmode == "mixin":
                playlist = mixin(playlist, result)
                msg = "%d files mixed into playlist " % count
            elif self.lmode == "replace":
                playlist = result
                msg = "playlist replaced with %d files " % count
            elif self.lmode == "prepend":
                playlist = result + playlist
                msg = "%d files prepended to playlist " % count
            else:
                playlist = playlist + result
                msg = "%d files appended to playlist " % count
            proxy.replace([Binary(i) for i in playlist])
            self.message += msg + "from stored playlist '%s'. " % self.file
        else:
            self.message += "Weird error -- no filename name given. "

    def _do_loop(self):
        """toggle loop mode"""
        proxy.toggle_loop_mode()

    def _do_main(self):
        """switch to main view"""
        self.view = "standard"

    def _do_manual(self):
        """help command: display module docstring"""
        self.dyn_content += "<pre>\n" + __doc__ + "\n</pre>\n"

    def _do_memo(self):
        """memorize current track"""
        current_track = proxy.current().data
        if not current_track:
            self.message += "There is currently no track playing that can be memorized. "
        else:
            try:
                file = open(memo_file, "a")
                # seek end of file
                file.seek(0,2)
            except IOError:
                self.message += "Can not access MEMO file '%s'. " % memo_file
                return
            display = current_track.split('/')
            display = display[-1:]
            file.write('#EXTINF:-1,%s\n' % display)
            file.write("%s\n" % current_track)
            file.close()
            self.message += "Track '%s' added to memo file (%s). " % (current_track.replace('/', ' / '), memo_file)

    def _do_mixin(self):
        """mix all files from directory tree into playlist"""
        if self.dir:
            dir = self.dir
            #files = os.popen('find "%s" -type f -print' % dir).readlines()
            files = getfiles(dir)
            files.sort()
            count = 0
            result = []
            for file in files:
                file = string.strip(file)
                if file_is_moosical(file) and string.find(file, "/.") < 0:
                    result.append(file)
                    count += 1
            playlist = [i.data for i in proxy.list()]
            playlist = mixin(playlist, result)
            proxy.replace([Binary(i) for i in playlist])
            self.message += "%d files mixed into playlist from directory '%s'. " % (count,dir[len(myroot)+1:])
        else:
            self.message += "Weird error -- no directory name given. "

    def _do_moo(self):
        """moo command"""
        self.message += ";-)"
        self.dyn_content += "<pre>\n%s\n</pre>\n" % moo()

    def _do_move_top(self):
        """move selected file to top of playlist"""
        self.move_helper(-1)

    def _do_move_bottom(self):
        """move selected file to bottom of playlist"""
        self.move_helper(1)

    def _do_pause(self):
        """toggle pause state"""
        if self.is_paused:
            proxy.unpause()
        else:
            proxy.pause()

    def _do_play(self):
        """play command"""
        proxy.run_queue()
        proxy.unpause()

    def _do_play_last(self):
        """add selected file to bottom of playlist"""
        proxy.prepend([Binary(self.file)])
        self.message += "Track '%s' appended to playlist. " % format_name(self.file)

    def _do_play_next(self):
        """add selected file to top of playlist"""
        proxy.prepend([Binary(self.file)])
        self.message += "Playing next track '%s'. " % format_name(self.file)

    def _do_play_now(self):
        """play immediately selected file"""
        proxy.stop()
        proxy.prepend([Binary(self.file)])
        proxy.run_queue()
        self.message += "Now playing track '%s'. " % format_name(self.file)

    def _do_playlist(self):
        """switch to playlist view mode"""
        self.view = "playlist"

    def _do_prepend(self):
        """add selected file to top of playlist"""
        proxy.prepend([Binary(self.file)])
        self.message += "Track '%s' prepended to playlist. " % format_name(self.file)

    def _do_refresh(self):
        """do nothing but refresh current page"""
        pass

    def _do_remove(self):
        """remove selected file from playlist"""
        self.move_helper(0)

    def _do_rescan(self):
        """rescan jukebox directory"""
        global tree, playlists, parent, length
        tree, playlists, parent = recurse(myroot, {}, [], {myroot : None})
        tree, length, playlists = cleanup(tree, playlists)
        dump_data()
        self.message += '''Scan of jukebox directory '%s' completed. <br>
                           Found %d music files in %d directories and %d playlists. ''' % \
                           (myroot, length[myroot], len(tree), len(playlists))

    def _do_reset_form(self):
        """clear search form"""
        self.pattern=""

    def _do_reverse(self):
        """reverse playlist"""
        proxy.reverse()

    def _do_search(self):
        """switch to search view mode"""
        self.view="search"

    def _do_shuffle(self):
        """randomize playlist order"""
        oldlist = [i.data for i in proxy.list()]
        newlist = []
        while oldlist:
            index = random.randint(0,len(oldlist)-1)
            newlist.append(oldlist[index])
            del oldlist[index]
        proxy.replace([Binary(i) for i in newlist])

    def _do_skip(self):
        """skip forward/backward a given number of tracks"""
        if self.is_looping and not self.queue_length:
            self.message += "The playlist is currently empty. "
        elif self.count > 0:
            self.next(self.count)
            self.message += "Command 'skip(%s)' executed. " % (self.count)
        elif self.count < 0:
            self.previous(-self.count)
            self.message += "Command 'skip(%s)' executed. " % (self.count)
        else:
            self.message += "Weird error -- no count given for skip. "

    def _do_sort(self):
        """sort playlist"""
        proxy.sort()

    def _do_stop(self):
        """stop command"""
        proxy.stop()

    def _do_tree(self):
        """switch to tree view mode"""
        self.view = "tree"

    def _do_tskip(self):
        """
        Skip forward or backward a given number of positions.
        Take precaution if moosicd advanced one or more tracks
        since the page that generated this request was generated.
        """
        if self.count and self.file:
            # stop forwarding in order no to mess things up
            proxy.halt_queue()
            count = self.count
            file  = self.file
            if count > 0:
                # seek new offset in case playlist changed
                offset = self.offset_plist(count-1, file)
                if offset >= 0:
                    self.next(offset+1)
                    self.message += "Skipped forward to track '%s'. " % format_name(file)
                else:
                    self.message += """<font color="#880000">The requested track '%s' is not
                                       available at the assumed position in the playlist and
                                       seems to have been played recently. </font>""" % format_name(file)
            elif count < 0:
                # seek new offset in case check history changed
                offset = self.offset_hist(-1-count, file)
                if offset >= 0:
                    self.previous(offset+1)
                    self.message += "Skipped back to track '%s'. " % format_name(file)
                else:
                    self.message += """<font color="#880000">The history buffer
                                      is outdated. File '%s' is not available in the history. </font>""" % format_name(file)
            else:
                self.message += "No tracks skipped. How did you come here anyway? "
            # start forwarding if it was previously enabled
            if self.is_queue_running:
                proxy.run_queue()
                time.sleep(0.05)
        else:
            self.message += "Weird error -- no count or filename given for skip. "

    #-------------------------------------------

    def cont_standard(self):
        """prepare contents for standard view mode: playlist and history"""
        playlist = [i.data for i in proxy.list()[:10]]
        content  = ['<table border="0" width="100%" cellspacing="0" cellpadding="0"><tr><td width="50%" valign="top">\n']
        content.append('<table class="menu" border="0" width="100%" cellspacing="0">\n')
        content.append('<tr><th colspan="2" align="left">Playlist</th></tr>\n')
        i=1
        for f in playlist:
            content.append('<tr><td class="%s" valign="top" align="right">[%d]&nbsp;&nbsp;&nbsp;</td><td class="%s" width="95%%">%s</td></tr>\n' % (klass[i & 1], i, klass[i & 1], format_name("%s" % f)))
            i += 1
        if not playlist:
            content.append('<tr><td colspan="2">(The playlist is currently empty.)</td></tr>\n')
        content.append("</table>\n")
        content.append('</td><td width="1%"> </td>\n')

        history = proxy.history(10)
        history.reverse()
        content.append('<td width="49%" valign="top"><table class="menu" border="0" width="100%" cellspacing="0">\n')
        content.append('<tr><th colspan="2" align="left">History</th></tr>\n')
        i=-1
        for f in history:
            content.append('<tr><td class="%s" valign="top" align="right">[%d]&nbsp;&nbsp;&nbsp;</td><td class="%s" width="95%%">%s</td></tr>\n' % (klass[i & 1],i,klass[i & 1],format_name("%s" % f[0])))
            i -=1
        if not history:
            content.append('<tr><td colspan="2">(The history buffer is currently empty.)</td></tr>\n')
        content.append("</table>\n")
        content.append("</td></tr></table>\n")
        return ''.join(content)

    def cont_history(self):
        """prepare contents for history view mode"""
        history = proxy.history()
        history.reverse()
        content = ['<table class="menu" border="0" width="100%" cellspacing="0">\n']
        content.append('<tr><th width="90%" align="left" valign="middle">History</th>\n')
        content.append('<th align="right" valign="middle">%s</th><th valign="middle">@@cform</th></tr>\n' % (search_form % ("refresh", self.view, self.mypath, self.pattern,"search history")))
        content.append("</table>\n")
        content.append('<table class="menu" border="0" width="100%" cellspacing="0">\n')
        i=-1
        count = 0
        files = [str(f[0]) for f in history]
        looping = proxy.is_looping()
        for f in files:
            if match(f[len(myroot):], string.translate(self.pattern, xlat)):
                content.append('<tr>')
                content.append('<td class="%s" valign="top" align="right">[%d]&nbsp;&nbsp;&nbsp;</td>\n' % (klass[count & 1],i))
                if looping:
                    content.append('<td colspan="5" class="%s" width="90%%" valign="top">%s</td>\n' % (klass[count & 1],format_name(f)))
                else:
                    content.append('<td class="%s" width="60%%" valign="top">%s</td>\n' % (klass[count & 1],format_name(f)))
                    content.append('<td class="%s" valign="top"><a href="tskip?@@params&amp;count=%d&amp;file=%s">skip</a>&nbsp;</td>\n' % (klass[count & 1],i, urllib.quote(f)))
                    content.append('<td class="%s" valign="top"><a href="play_now?@@params&amp;file=%s">play</a>&nbsp;</td>\n' % (klass[count & 1],urllib.quote(f)))
                    content.append('<td class="%s" valign="top"><a href="play_next?@@params&amp;file=%s">top</a>&nbsp;</td>\n' % (klass[count & 1],urllib.quote(f)))
                    content.append('<td class="%s" valign="top"><a href="play_last?@@params&amp;file=%s">bottom</a></td>\n' % (klass[count & 1],urllib.quote(f)))
                content.append('</tr>')
                count += 1
            i -= 1
        if not history:
            content.append('<tr><td colspan="6">(The history buffer is currently empty.)</td></tr>\n')
        elif count == 0:
            content.append('''<tr><td colspan="6">(no entries in history matching '%s')</td></tr>\n''' % self.pattern)
        content.append("</table>\n")
        return ''.join(content)

    def cont_playlist(self):
        """prepare contents for playlist view mode"""
        playlist = [i.data for i in proxy.list()]
        content = ['<table class="menu" border="0" width="100%" cellspacing="0">\n']
        content.append('<tr><th width="90%" align="left" valign="middle">Playlist @@LIMIT</th>\n')
        content.append('<th align="right" valign="middle">%s</th><th valign="middle">@@cform</th></tr>\n' % (search_form % ("refresh", self.view, self.mypath, self.pattern,"search playlist" )))
        content.append("</table>\n")
        content.append('<table class="menu" border="0" width="100%" cellspacing="0">\n')
        i = 1
        count = 0
        for f in playlist:
            if match(f[len(myroot):], string.translate(self.pattern, xlat)):
                if count < limit:
                    content.append('<tr>\n')
                    content.append('<td class="%s" valign="top" align="right">[%d]&nbsp;&nbsp;&nbsp;</td>\n' % (klass[count & 1],i))
                    content.append('<td class="%s" width="60%%" valign="top">%s</td>\n' % (klass[count & 1],format_name(f)))
                    content.append('<td class="%s" valign="top"><a href="tskip?@@params&amp;count=%d&amp;file=%s">skip</a>&nbsp;</td>\n' % (klass[count & 1],i, urllib.quote(f)))
                    if proxy.is_looping():
                        content.append('<td class="%s"> </td>' % klass[count & 1])
                    else:
                        content.append('<td class="%s" valign="top"><a href="play_now?@@params&amp;file=%s">play</a>&nbsp;</td>\n' % (klass[count & 1],urllib.quote(f)))
                    content.append('<td class="%s" valign="top"><a href="move_top?@@params&amp;pos=%d&amp;file=%s">top</a>&nbsp;</td>\n' % (klass[count & 1],i-1, urllib.quote(f)))
                    content.append('<td class="%s" valign="top"><a href="move_bottom?@@params&amp;pos=%d&amp;file=%s">bottom</a>&nbsp;</td>\n' % (klass[count & 1],i-1, urllib.quote(f)))
                    content.append('<td class="%s" valign="top"><a href="remove?@@params&amp;pos=%d&amp;file=%s">remove</a>&nbsp;</td>\n' % (klass[count & 1],i-1, urllib.quote(f)))
                    content.append('</tr>')
                count += 1
            i += 1
        if not playlist:
            content.append('<tr><td colspan="7">(The playlist is currently empty.)</td></tr>\n')
        elif count == 0:
            content.append('''<tr><td colspan="7">(no entries in playlist matching '%s')</td></tr>\n''' % self.pattern)
        content.append("</table>\n")

        if self.pattern: text="matches"
        else: text="entries"
        content = ''.join(content)
        if count >= limit:
            content = string.replace(content, "@@LIMIT", "(showing %d of %d %s.)" % (limit,count,text))
        else:
            content = string.replace(content, "@@LIMIT", "(%d %s.)" % (count,text))
        return content

    def cont_files(self):
        """prepare contents for file view mode"""

        files = tree[self.mypath]
        dirs = [dir for dir in tree.keys() if parent[dir]==self.mypath]
        dirs.sort()
        temp=string.split(myroot,"/")
        temp = temp.pop()
        temp = temp + self.mypath[len(myroot):]

        content = ['<table class="menu" border="0" width="100%" cellspacing="0">\n']
        content.append('<tr><th align="left" colspan="6">%s</th></tr>\n'  % temp)
        content.append('<tr><td class="thsub" colspan="3"><i>Subdirectories</i></td>\n')
        if len(self.mypath) > len(myroot):
            newdir = string.split(self.mypath,"/")
            newdir.pop()
            newdir = string.join(newdir,"/")
            uplink = '<td class="thsub" align="right" colspan="3"><a href="chdir?@@params&amp;dir=%s">.. (up to parent directory)</a></td></tr>\n' % urllib.quote(newdir)
        else:
            uplink = '<td class="thsub" align="left" colspan="3">&nbsp;</td></tr>\n'
        content.append(uplink)
        count = 0
        for f in dirs:
             if string.find(f,"/.") < 0:
                nfiles = length[f]
                dir = string.split(f,"/").pop()
                content.append('<tr>')
                content.append('<td class="%s" width="40%%" valign="top"><a href="chdir?@@params&amp;dir=%s">%s</a></td>\n' % (klass[count & 1],urllib.quote(f), dir))
                content.append('<td class="%s" valign="top" align="right">%d music&nbsp;files&nbsp;&nbsp;&nbsp;&nbsp;</td>\n' % (klass[count & 1],nfiles))
                content.append('<td class="%s" valign="top"> </td>\n' % klass[count & 1])
                content.append('<td class="%s" valign="top"><a href="mixin?@@params&amp;dir=%s">mixin</a>&nbsp;</td>\n' % (klass[count & 1],urllib.quote(f)))
                content.append('<td class="%s" valign="top"><a href="add_top?@@params&amp;dir=%s">prepend</a>&nbsp;</td>\n' % (klass[count & 1],urllib.quote(f)))
                content.append('<td class="%s" valign="top"><a href="add_bottom?@@params&amp;dir=%s">append</a>&nbsp;</td>\n' % (klass[count & 1],urllib.quote(f)))
                content.append('</tr>\n')
                count += 1
        if count == 0:
            content.append('<tr><td colspan="6">(no subdirectories)</td></tr>\n')
        content.append('<tr><td colspan="6">&nbsp;</td></tr>\n')
        content.append("</table>\n")

        content.append('<table class="menu" border="0" width="100%" cellspacing="0">\n')
        content.append('<tr><td class="thsub" align="left" colspan="4"><i>Music files</i></td></tr>\n')
        count = 0
        for file in files:
            f = self.mypath + "/" + file
            if file_is_moosical(file) and f[:1] != ".":
                content.append('<tr>\n')
                content.append('<td class="%s" width="40%%" valign="top">%s</td>\n' % (klass[count & 1],file))
                if proxy.is_looping():
                    content.append('<td class="%s">&nbsp;</td>' % klass[count & 1])
                else:
                    content.append('<td class="%s" valign="top"><a href="play_now?@@params&amp;file=%s">play</a>&nbsp;</td>\n' % (klass[count & 1],urllib.quote(f)))
                content.append('<td class="%s" valign="top"><a href="prepend?@@params&amp;file=%s"?>prepend</a>&nbsp;</td>\n' % (klass[count & 1],urllib.quote(f)))
                content.append('<td class="%s" valign="top"><a href="append?@@params&amp;file=%s">append</a>&nbsp;</td>\n' % (klass[count & 1],urllib.quote(f)))
                content.append('</tr>')
                count += 1

        if count == 0:
            content.append('''<tr><td colspan="4">(no music files)</td></tr>\n''')

        content.append("</table>\n")

        return ''.join(content)

    def cont_tree(self):
        """prepare contents for (directory) tree view mode"""
        dirs = tree.keys()
        dirs.sort()
        content =  ['<table class="menu" border="0" width="100%" cellspacing="0">\n']
        content.append('<tr><th align="left" colspan="5">Jukebox directory %s</th></tr>\n' % myroot)
        count = 0
        for dir in dirs:
            temp = string.split(myroot,"/")
            chunks = string.split(dir,"/")
            last = chunks[-1]
            depth = len(chunks) - len(temp)
            content.append('<tr>\n')
            content.append('<td class="%s" width="70%%" valign="top">%s<a href="chdir?@@params&amp;dir=%s">%s</a></td>\n' % (klass[count & 1], '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;' * depth, urllib.quote(dir), last))
            content.append('<td class="%s" valign="top" align="right">%d&nbsp;music&nbsp;files&nbsp;&nbsp;&nbsp;</td>\n' % (klass[count & 1],length[dir]))
            content.append('<td class="%s" valign="top"><a href="mixin?@@params&amp;dir=%s">mixin</a>&nbsp;</td>\n' % (klass[count & 1],urllib.quote(dir)))
            content.append('<td class="%s" valign="top"><a href="add_top?@@params&amp;dir=%s">prepend</a>&nbsp;</td>\n' % (klass[count & 1],urllib.quote(dir)))
            content.append('<td class="%s" valign="top"><a href="add_bottom?@@params&amp;dir=%s">append</a>&nbsp;</td>\n' % (klass[count & 1],urllib.quote(dir)))
            content.append('</tr>\n')
            count += 1
        content.append("</table>\n")

        return ''.join(content)

    def cont_search(self):
        """prepare contents for search view mode"""
        dirs = tree.keys()
        dirs.sort()
        mdirs = []
        mfiles = []
        mpattern = string.translate(self.pattern,xlat)
        content = ['<table class="menu" border="0" width="100%" cellspacing="0">\n']
        content.append('''<tr><th align="left" colspan="5">Search result for '%s'</th></tr>\n''' % self.pattern)
        for dir in dirs:
            if string.find(dir,"/.") < 0:
                temp = string.split(dir,"/")
                temp = temp.pop()
                if match(temp, mpattern):
                    mdirs.append(dir)
                files = tree[dir]
                for file in files:
                    if file_is_moosical(file) and file[:1] != "." \
                            and match(file, mpattern):
                        mfiles.append(dir + "/" + file)

        ndirs = len(mdirs)
        if ndirs > limit:
            mdirs = mdirs[0:limit]
            content.append('<tr><td class="thsub" colspan="5"><i>Directories (showing %d of %d matches.)</i></td></tr>\n' % (limit, ndirs))
        else:
            content.append('<tr><td class="thsub" colspan="5"><i>Directories (%d matches.)</i></td></tr>\n' % (ndirs))

        count = 0
        for dir in mdirs:
            temp = string.split(myroot,"/")
            chunks = string.split(dir,"/")
            last = chunks[-1]
            depth = len(chunks) - len(temp)
            content.append('<tr>\n')
            content.append('<td class="%s" width="70%%" valign="top"><a href="chdir?@@params&amp;dir=%s">%s</td>\n' % (klass[count & 1],urllib.quote(dir), format_name(dir)))
            content.append('<td class="%s" valign="top" align="right">%d&nbsp;music&nbsp;files&nbsp;&nbsp;</td>\n' % (klass[count & 1],length[dir]))
            content.append('<td class="%s" valign="top"><a href="mixin?@@params&amp;dir=%s">mixin</a>&nbsp;</td>\n' % (klass[count & 1],urllib.quote(dir)))
            content.append('<td class="%s" valign="top"><a href="add_top?@@params&amp;dir=%s">prepend</a>&nbsp;</td>\n' % (klass[count & 1],urllib.quote(dir)))
            content.append('<td class="%s" valign="top"><a href="add_bottom?@@params&amp;dir=%s">append</a>&nbsp;</td>\n' % (klass[count & 1],urllib.quote(dir)))
            content.append('</tr>\n')
            count += 1
        if len(mdirs) == 0:
            content.append('<tr><td colspan="5">(no directories found)</td></tr>\n')
        content.append('<tr><td colspan="5">&nbsp;</td></tr>\n')
        content.append("</table>\n")

        content.append('<table class="menu" border="0" width="100%" cellspacing="0">\n')
        nfiles = len(mfiles)
        if nfiles > limit:
            mfiles = mfiles[0:limit]
            content.append('<tr><td class="thsub" colspan="4"><i>Music files (showing %d of %d matches.)</i></td></tr>\n' % (limit, nfiles))
        else:
            content.append('<tr><td class="thsub" colspan="4"><i>Music files (%d matches.)</i></td></tr>\n' % (nfiles))
        count = 0
        for file in mfiles:
            content.append('<tr>\n')
            content.append('<td class="%s" width="80%%" valign="top">%s</td>\n' % (klass[count & 1],format_name(file)))
            if proxy.is_looping():
                content.append('<td class="%s"> </td>' % (klass[count & 1]))
            else:
                content.append('<td class="%s" valign="top"><a href="play_now?@@params&amp;file=%s">play</a>&nbsp;</td>\n' % (klass[count & 1],urllib.quote(file)))
            content.append('<td class="%s" valign="top"><a href="prepend?@@params&amp;file=%s"?>prepend</a>&nbsp;</td>\n' % (klass[count & 1],urllib.quote(file)))
            content.append('<td class="%s" valign="top"><a href="append?@@params&amp;file=%s">append</a>&nbsp;</td>\n' % (klass[count & 1],urllib.quote(file)))
            content.append('</tr>')
            count += 1
        if nfiles == 0:
            content.append('<tr><td colspan="4">(no files found)</td></tr>\n')
        content.append("</table>\n")
        return ''.join(content)

    #-------------------------------------------

    def listPL(self, file):
        """list content of playlist (without .m3u specific comments)"""
        print "PL FILE", file
        try:
            lines = open(file,"r").readlines()
        except IOError:
            self.message += "Can not read playlist '%s'. " % file
        else:
            lines = [line for line in lines if line[:1] != '#']
            content = ['<table class="menu" border="0" width="100%" cellspacing="0">\n']
            content.append('''<tr><th align="left">Content of playlist '%s'</th></tr>\n''' % file[len(myroot)+1:])
            count = 0
            for line in lines:
                content.append('<tr>')
                content.append('<td class="%s">%s</td>\n' % (klass[count&1], format_name(line)))
                content.append('</tr>\n')
                count += 1
            if not lines:
                content.append('<tr><td class="%s">(empty playlist)</td></tr>' % klass[0])
            content.append("</table>\n")
            self.message += "Playlist '%s' contains %d entries.<br>Options: " % (file[len(myroot)+1:], len(lines))
            self.message += '<a href="load_pl?@@params&amp;file=%s&amp;lmode=replace">replace&nbsp;PL</a>, ' % (urllib.quote(file))
            self.message += '<a href="load_pl?@@params&amp;file=%s&amp;lmode=mixin">mixin</a>, ' % (urllib.quote(file))
            self.message += '<a href="load_pl?@@params&amp;file=%s&amp;lmode=prepend">prepend</a> or ' % (urllib.quote(file))
            self.message += '<a href="load_pl?@@params&amp;file=%s&amp;lmode=append">append</a>' % (urllib.quote(file))

            self.dyn_content = ''.join(content)

    def move_helper(self, new):
        """move selected file to top or bottom of playlist or remove file from playlist"""
        if self.file:
            # stop forwarding in order no to mess things up
            proxy.halt_queue()
            pos  = self.pos
            file = self.file
            # seek new offset in case check playlist changed
            offset = self.offset_plist(pos, file)
            if offset >= 0:
                try:
                    playlist=self.playlist
                except AttributeError:
                    playlist = [i.data for i in proxy.list()]
                del playlist[offset]
                if new > 0:
                    playlist = playlist + [file]
                    self.message += "Track '%s' moved to bottom of playlist. " % format_name(file)
                elif new < 0:
                    playlist = [file] + playlist
                    self.message += "Track '%s' will be played next. " % format_name(file)
                else:
                    self.message += "Track '%s' removed from playlist. " % format_name(file)
                proxy.replace([Binary(i) for i in playlist])
            else:
                self.message += """<font color="#880000">The requested file '%s' is not
                                    available at the assumed position in the playlist and
                                    seems to have been played recently. </font>""" % format_name(file)
            # start forwarding if it was previously enabled
            if self.is_queue_running:
                proxy.run_queue()
        else:
            self.message += "Weird error -- no count or filename given. "

    def next(self, count):
        """kludge to work around bug in xmlrpclib or moosicd"""
        while True:
            try:
                proxy.next(count)
                return
            except:
                time.sleep(0.05)
                pass

    def offset_hist(self, pos, file):
        """seek new offset of file in history"""
        history = proxy.history()
        history.reverse()
        max = len(history)
        while pos < max:
            entry = history[pos]
            hfile = str(entry[0])
            if file == hfile:
                return pos
            pos += 1
        return -1

    def offset_plist(self, pos, file):
        """seek new offset of file in playlist"""
        plist = [i.data for i in proxy.list()]
        while pos >= 0:
            if file == plist[pos]:
                return pos
            pos -= 1
        return -1

    def previous(self, count):
        """kludge to work around bug in xmlrpclib or moosicd"""
        while True:
            try:
                proxy.previous(count)
                return
            except:
                time.sleep(0.05)
                pass

class Error(Exception):
    pass

class SubnetError(Error):
    def __init__(self, subnet):
        self.subnet = subnet
    def __str__(self):
        return "Invalid subnet: " + str(self.subnet)

class SubnetIPError(Error):
    def __init__(self, ip):
        self.ip = ip
    def __str__(self):
        return "Invalid IP: " + str(self.ip)

class subnet:
    def __init__(self, subnet_cidr):
        if not re.compile(r'^[0-9]{1,3}(\.[0-9]{1,3}){0,3}/[0-3]*[0-9]?$').match(subnet_cidr):
            raise SubnetError, subnet_cidr
        [cidr_subnet_ip, cidr_mask] = subnet_cidr.split('/')

        cidr_mask = int(cidr_mask)
        if cidr_mask < 0 or cidr_mask > 32:
            raise SubnetError, subnet_cidr
        subnet_mask_int = 0
        for bit_num in range(32 - cidr_mask, 33):
            subnet_mask_int += 2**bit_num

        cidr_subnet_ip_nums = cidr_subnet_ip.split('.')
        cidr_subnet_int = 0
        for number in cidr_subnet_ip_nums:
            cidr_subnet_int = cidr_subnet_int * 256 + int(number)
        for index in range(0, 4 - len(cidr_subnet_ip_nums)):
            cidr_subnet_int = cidr_subnet_int * 256

        self.subnet_int = cidr_subnet_int
        self.subnet_ip = cidr_subnet_ip
        self.subnet_mask_int = subnet_mask_int
        self.address_mask_int = 4294967295 ^ subnet_mask_int
        self.cidr_mask = cidr_mask

        if(self.subnet_int & self.subnet_mask_int != self.subnet_int):
            raise SubnetError, subnet_cidr
    def get_cidr(self):
        return self.subnet_ip, self.cidr_mask
    def get_int(self):
        return self.subnet_int, self.subnet_mask_int
    def ip_is_member(self, ip_address):
        if not re.compile(r'^[0-9]{1,3}(\.[0-9]{1,3}){3,3}$').match(ip_address):
            raise SubnetIPError, ip_address
        ip_address = ip_address.split('.')
        ip_address_int = 0
        for number in ip_address:
            ip_address_int = ip_address_int * 256 + int(number)
        ip_subnet_int = ip_address_int & self.subnet_mask_int
        if ip_subnet_int != self.subnet_int:
            return False
        return True
    def __str__(self):
        return self.subnet_ip + '/' + str(self.cidr_mask)
    def __repr__(self):
        return self.__str__()

# Subroutines

def moo():
    """create contents for moo command"""
    # taken from moosic CLI client, file dispatcher.py
    return base64.decodestring('''\
ICAgICAgICAoX19fKSAgIChfX18pICAoX19fKSAoX19fKSAgICAgIChfX18pICAgKF9fXykgICAo
X19fKSAoX19fKSAgICAgCiAgICAgICAgKG8gbyhfX18pbyBvKShfX18pbykgKG8gbykgKF9fXyko
byBvKF9fXylvIG8pKF9fXykgbykgKG8gbykoX19fKQogICAgICAgICBcIC8obyBvKVwgLyAobyBv
KS8gKF9fXykgIChvIG8pIFwgLyhvIG8pXCAvIChvIG8pIC8oX19fKS8gKG8gbykKICAgICAgICAg
IE8gIFwgLyAgTyAgIFwgL08gIChvIG8pICAgXCAvICAgTyAgXCAvICBPICAgXCAvIE8gKG8gbykg
ICBcIC8gCiAgICAgICAgKF9fKSAgTyAoPT0pICAgTyhfXykgXCAvKHx8KSBPICAoX18pICBPIChf
XykgICAgKCAgKSBcIC8oX18pIE8gIAogICAgICAgIChvbykoX18pKG9vKShfXykob28pKF9fKShv
bykoX18pKG9vKShfXykoIyMpKF9fKShvbykoX18pKG9vKShfXykKICAgICAgICAgXC8gKG9vKSBc
LyAob28pIFwvICgsLCkgXC8gKG9vKSBcLyAob28pIFwvIChvbykgXC8gKC0tKSBcLyAoT08pCiAg
ICAgICAgKF9fKSBcLyAoX18pIFwvIChfXykgXC8gKF9fKSBcLyAoX18pIFwvIChfXykgXC8gKCws
KSBcLyAoX18pIFwvIAogICAgICAgICgqKikoX18pKC0tKShfXykob28pKF9fKSgwMCkoX18pKG9v
KShfXykob28pKF9fKShvbykoX18pKG9vKShfXykKICAgICAgICAgXC8gKG9vKSBcLyAob28pIFwv
IChvbykgXC8gKG9vKSBcLyAoKiopIFwvIChPTykgXC8gKD8/KSBcLyAob28pCiAgICAgICAgKF9f
KSBcLyAoX18pIFwvIChfXykgXC8gKF9fKSBcLyAoX18pIFwvIChfXykgXC8gKF9fKSBcLyAoX18p
IFwvIAogICAgICAgIChvbykoX18pKG9vKShfXykoQEApKF9fKShvbykoX18pKG9vKShfXykob28p
KF9fKSgtMCkoLCwpKG9vKShfXykKICAgICAgICAgXC8gKG9fKSBcLyAob28pIFwvIChvbykgXC8g
KG8jKSBcLyAob28pIFwvIChvbykgXC8gKG9vKSBcLyAob28pCiAgICAgICAgICAgICBcLyAgICAg
IFwvICAgICAgXC8gICAgICBcLyAgICAgIFwvICAgICAgXC8gICAgICBcLyAgICAgIFwvIAogICAg
ICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAg
ICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAg
ICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAoX18pICAgICAgICAgICAg
ICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAs
Jy0wMCAgICAgICAgICAgICAgICAgICAgICAgVGhlIExvY2FsIE1vb3NpY2FsIFNvY2lldHkgICAg
ICAKICAgICAgICAgICAvIC9cX3wgICAgICAvICAgICAgICAgICAgICAgICAgICAgICBpbiBDb25j
ZXJ0ICAgICAgICAgICAgICAgCiAgICAgICAgICAvICB8ICAgICAgIF8vX19fX19fX19fX19fX19f
X19fICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICB8ICAgXD09PV5fX3wg
ICAgICAgICAgICAgICAgIF9ffCAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAg
ICBffF9fXyAvXCAgfF9fX19fX19fX19fX19fX19fX198ICAgICAgICAgICAgICAgICAgICAgICAg
ICAgICAgICAgCiAgICAgICAgfD09PT09fCB8ICAgSSAgICAgICAgICAgICAgSSAgICAgICAgICAg
ICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICpJICAgSXwgfCAgIEkgICAgICAgICAg
ICAgIEkgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgSSAgIEle
IF4gICBJICAgICAgICAgICAgICBJICAgICAgICAgICAgICAgICAgICAgLWNmYmQt''')


def usage():
    """print help message"""
    print >> sys.stderr, """
usage:
    %s [-p number] [-s] [-j name] [-a host] [-n net] [-h]
    [-m] [-d] [-c configdir] [-t template] [--port=number] [--server-only]
    [--jukebox-dir=name] [--add-host=host] [--add-network=net] [--help]
    [--manual] [--debug] [--config=dir] [--template=file]

options:
    -p number, --port=number     set the server's portnumber to number
    -s, --server-only            server-only mode, no browser launched
    -j name, --jukbox-dir=name   set jukebox directory to name
    -a host, --add-host=host     add host to list of allowed hosts
    -n net, --add-network=net    add network to list of allowed networks
                                 (use CIDR notation, e.g. 192.168.0.0/24)
    -h, --help                   display help message
    -m, --manual                 display manual page
    -d, --debug                  include debug information in HTML page
    -c dir, --config=dir         use moosic configuration in directory dir
    -t file, --template=file     use alternate HTML template file
""" % progname


def format_name(s):
    """format path name: avoid overly wide html pages due to large filename length"""
    s=s[len(myroot)+1:]
    s=string.replace(s,"/","&nbsp;/ ")
    s=string.replace(s,"_","&nbsp;")
    s=string.replace(s,"--"," -- ")
    return s


def match(st, pat):
    """somewhat fuzzy name matcher"""
    st = string.translate(st, xlat)
    st = string.replace(st, " ", "")
    pat= string.replace(pat, " ", "")
    return string.find(st, pat) >= 0


def mixin(l1,l2):
    """intermix two lists"""
    if not l1: return l2
    if not l2: return l1
    quot = float(len(l1)) / float(len(l2))
    list1 = l1[:]
    list2 = l2[:]
    result = []
    while list1 and list2:
        if float(len(list1)) / float(len(list2)) > quot:
            result.append(list1.pop())
        else:
            result.append(list2.pop())
    while list1:
        result.append(list1.pop())
    while list2:
        result.append(list2.pop())
    result.reverse()
    return result


def recurse(dir, tree, playlists, parent):
    """read directory tree and store entries in dictionary"""
    # global tree, playlists
    try:
        entries = os.listdir(dir)
    except OSError:
        # omit dirs without sufficient permission
        return tree, playlists, parent
    dirs=[]
    files=[]
    for entry in entries:
        # omit symlinks and hidden entries
        pathname = dir+"/"+entry
        if not os.path.islink(pathname) and entry[:1] != ".":
            if os.path.isdir(pathname):
                dirs.append(entry)
            elif os.path.isfile(pathname):
                if pathname.endswith(".m3u"):
                    playlists.append(pathname)
                elif file_is_moosical(pathname):
                    files.append(entry)
    files.sort()
    tree[dir]=files
    for d in dirs:
        parent[dir + "/" + d] = dir
        tree, playlists, parent = recurse(dir + "/" + d, tree, playlists, parent)
    return tree, playlists, parent

def cleanup(tree, playlists):
    ''' remove dirs containing no music files and invisible dirs from hash,
        calculate total number of music files in subtrees.
    '''
    length={}
    for dir in tree.keys():
        l = 0
        for sd in tree.keys():
            if sd[:len(dir)] == dir:
                l += len(tree[sd])
        if l == 0 or string.find(dir,"/.") >= 0:
            del tree[dir]
        else:
            length[dir]=l
    # we rely on having at least an entry for the jukebox directory ...
    if tree == {}:
        tree = {myroot: []}
        length[myroot] = 0

    playlists.sort()
    global memo_file
    playlists.append(memo_file)
    return tree, length, playlists

def getfiles(dir):
    """get all files in directory tree from dictionary"""
    files = []
    dirs = tree.keys()
    dirs.sort()
    for d in dirs:
        if d[0:len(dir)] == dir:
            for file in tree[d]:
                files.append(d + "/" + file)
    return files


def file_is_moosical(filename):
    ''' determine if a file is a 'moosical' file '''
    for regexp in moosic_regexps:
        if regexp.search(filename):
            return True
    return False


def read_moosic_config(filename):
    ''' read moosic config directory '''
    if not os.path.exists(filename):
        return None
    regexps = [ ]
    expecting_regex = True
    for line in fileinput.input(filename):
        # skip empty lines
        if re.search(r'^\s*$', line):
            continue
        # skip lines that begin with a '#' character
        if re.search('^#', line):
            continue
        # chomp off trailing newline
        if line[-1] == '\n':
            line = line[:-1]
        # the first line in each pair is interpreted as a regular expression
        # note that case is ignored. it would be nice if there was an easy way
        # for the user to choose whether or not case should be ignored.
        if expecting_regex:
            regexps.append(re.compile(line))
            expecting_regex = False
        # the second line in each pair is interpreted as a command
        else:
            expecting_regex = True
    return regexps


def allowed_to_connect(ip_address):
    ''' determine if a client is allowed to connect to webserver '''
    if ip_address in allowed_hosts:
        return True
    for subnet in allowed_networks:
        if subnet.ip_is_member(ip_address):
            return True
    return False


def tuple2ip(tuple):
    ip = ""
    for number in tuple:
        ip = ip + str(number)
    return ip


def dump_data():
    ''' dump data related to jukeboxdir to file in order to speed up next start'''
    try:
        outfile = open(dump_fn, "wb")
        marshal.dump((myroot, tree, parent, length, playlists), outfile)
        outfile.close()
    except:
        print >> sys.stderr, "\n+++ can not create data file '%s'.\n" % dump_fn


def load_dump():
    ''' load data related to jukeboxdir from file in order to speed start-up '''
    try:
        file = open(dump_fn, "rb")
        (te, tr, pa, le, pl)  = marshal.load(file)
        file.close()
        return (te, tr, pa, le, pl)
    except:
        print >> sys.stderr, "\n+++ can not read data file '%s'.\n" % dump_fn
        return ("", {}, {}, {}, [])



################################################################################
# MAIN PROGRAM
################################################################################

__version__      = '0.9'
progname         = 'moosicWebGUI'
version          = progname + ' version ' + __version__ + ' (2005-12-03)'

port             = 8000        # default server port
openbrowser      = True        # open browser after server start
debug            = False       # you guessed it
auto_inc         = True        # auto search for free port to connect to
ignore_exit      = False       # ignore exit requests
limit            = 250         # limit display to ... entries
allowed_hosts = ['127.0.0.1']  # allow only these hosts
allowed_networks = []

server_address   = ""
home             = os.getenv('HOME', '/tmp')
configdir        = os.path.join(home, ".moosic")
mydir, file      = os.path.split(os.path.abspath(sys.argv[0]))
myroot           = os.getenv('HOME', '/tmp')
tfn              = os.path.join(mydir,"template.html")

# scan command line options
try:
    optlist, args = getopt.getopt(sys.argv[1:], 'a:n:p:ij:shmdc:t:',
                    ["add-host=", "add-network=", "port=", "ignore-exit", \
                    "jukebox-dir=", "server-only", "help", "manual", "debug", \
                    "config=", "template="])
except getopt.GetoptError:
    usage()
    sys.exit(2)
for i, j in optlist:
    if i in ('-a', "--add-host"):
        try:
            h = socket.gethostbyname(j)
        except socket.aigerror:
            print >> sys.stderr, "\n*** DNS lookup for host '%s' failed.\n" % j
            sys.exit(1)
        else:
            allowed_hosts.append(h)
    elif i in ('-n', "--add-network"):
        try:
            sn = subnet(j)
        except SubnetError:
            print >> sys.stderr, "\n*** '%s' is not a valid network specification.\n" % j
            sys.exit(1)
        else:
            allowed_networks.append(sn)
    elif i in ('-p', "--port"):
        port = string.atoi(j)
        auto_inc = False
    elif i in ('-i', "--ignore-exit"):
        ignore_exit = True
    elif i in ('-j', "--jukebox-dir"):
        if j[:1] != "/":
            print >> sys.stderr, "\n*** Jukebox directory must be absolute pathname.\n"
            sys.exit(1)
            try:
                test = os.listdir(j)
            except OSError:
                print >> sys.stderr, "\n*** Error reading jukebox directory '%s'.\n" % j
                sys.exit(1)
        myroot = j
    elif i in ('-s', "--server-only"):
        openbrowser = None
    elif i in ('-h', "--help"):
        usage()
        sys.exit(0)
    elif i in ('-m', "--manual"):
        print __doc__
        sys.exit(0)
    elif i in ('-d','--debug'):
        debug = True
    elif i in ('-c', '--config'):
        try:
            test = os.listdir(j)
        except OSError:
            print >> sys.stderr, "\n*** Error reading moosic configuration directory '%s'.\n" % j
            sys.exit(1)
        configdir = j
    elif i in ('-t', '--template'):
        tfn = j

if args:
    usage()
    sys.exit(2)

print '\nThis is ' + version + '\n'

# remove trailing "/" from jukeboxdir, if any, and make sure that the jukebox dir is not /
while myroot.endswith("/"):
    myroot = myroot[:-1]
if not myroot:
    print >> sys.stderr, "\n*** Please specify a jukebox directory other than '/'.\n"
    sys.exit(1)

configfile = os.path.join(configdir, "config")
moosic_regexps = read_moosic_config(configfile)
if moosic_regexps is None:
    print >> sys.stderr, "\n*** moosic configuration file '%s' does not exist.\n" % configfile
    sys.exit(1)

klass = ["even", "odd"]

# build a character translation table for sloppy search
sfrom = '-ABCDEFGHIJKLMNOPQRSTUVWXYZ¦´¼¾ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞ' + \
        '_abcdefghijklmnopqrstuvwxyz¨µ¸½ßàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ'
sto   = ' abcdefghijklmnopqrstuvwxyzszoyaaaaaaaceeeeiiiidnoooooouuuuyy' + \
        ' abcdefghijklmnopqrstuvwxyzsmzosaaaaaaaceeeeiiiidnoooooouuuuyyy'
xlat  = string.maketrans(sfrom,sto)

search_form = """
<form method="get" action="%s">
<table>
<tr>
    <td>&nbsp;
        <input type="hidden" name="view" value="%s">
        <input type="hidden" name="path" value="%s">
    </td>
    <td><input type="text" size="30" name="pattern" value="%s"></td>
    <td>&nbsp;</td>
    <td><input type="submit" value="%s"></td>
    <td>&nbsp;</td>
</tr>
</table>
</form>
"""

clear_form = """
<form method="get" action="reset_form">
<table>
<tr>
    <td><input type="hidden" name="view" value="%s">
        <input type="hidden" name="path" value="%s">
        <input type="submit" value="reset">
    </td>
</tr>
</table>
</form>
"""

# read page template from a file (template shall be located in same dir as this file)
try:
    template= open(tfn).read()
except IOError:
    print >> sys.stderr, "\n*** Can't read template file '%s'.\n" % tfn
    sys.exit(1)

#make connection to locally running moosicd
proxy = moosic.client.factory.LocalMoosicProxy(configdir + "/socket")
try:
    proxy.no_op()
except socket.error, e:
    if e[0] in (errno.ECONNREFUSED, errno.ENOENT):
        # the server doesn't seem to be running, so let's try to start it
        print "--- The moosic server isn't running, so it is being started automatically."
        failure_reason = moosic.client.factory.startServer('moosicd', '-c', configdir)

        if failure_reason:
            print >> sys.stderr, "\n*** The moosicd server doesn't seem to be running, and it could" +\
                                 "\n    because \n    %s" % failure_reason
            sys.exit(1)
        else:
            # give moosicd time to start up.
            time.sleep(0.25)
            # test the server connection again
            try:
                proxy.no_op()
            except Exception, e:
                # it's time to give up.
                print >> sys.stderr, "\n*** An attempt was made to start the moosic server," +\
                                     "\n    but it still can't be contacted.\n" +\
                                     "%s: %s" % (str(e.__class__).split('.')[-1], e)
                sys.exit(1)
    else:
        print >> sys.stderr, "\n*** Socket error: %s\n" % e
        sys.exit(1)

# check moosic api version
api=proxy.api_version()
if api[0] < 1 or (api[0]==1 and api[1] < 7):
    print >> sys.stderr, "\n*** Moosic api version %d.%d is not supported (must be 1.7 or later).\n" % (api[0], api[1])
    sys.exit(1)

# start web server
for i in range(65536 - port):
    print "--- Webserver is trying to connect to port %d ... " % port
    try:
        server_address = ('', port)
        httpd = BaseHTTPServer.HTTPServer(server_address, moosicWebGUIHTTPRequestHandler)
    except socket.error, exc:
        # error code 98: Address already in use
        if exc.args[0] == 98 and auto_inc:
            port += 1
        else:
            print >> sys.stderr, "\n*** Can not connect to port %s -- %s.\n" % (port, exc.args[1])
            sys.exit(1)
    else:
        print "--- Webserver ready on port %d. " % port
        break

print "--- Hosts allowed to connect:" , allowed_hosts
print "--- Networks allowed to connect:" , allowed_networks

# try to create a memo file
memo_file = os.path.join(configdir, ".moosicWebGUI-memo.m3u")
try:
    file = open(memo_file, "r")
    file.close()
except IOError:
    try:
        file = open(memo_file, "w")
        file.write('#EXTM3U\n')
        file.close()
    except IOError:
        print >> sys.stderr, "\n+++ can not create MEMO file '%s'.\n" % memo_file

# make sure that the jukebox directory is accessible
print "--- Checking jukebox directory '%s'" % myroot
try:
    entries = os.listdir(myroot)
except OSError:
    # abort on errors
    print >> sys.stderr, "\n*** Can not access jukebox directory '%s'\n" % myroot
    sys.exit(1)

# load dumped data from file
dump_fn = os.path.join(configdir, ".moosicWebGUI-dump.dat")
print "--- Loading data from file '%s'" % dump_fn
temp, tree, parent, length, playlists = load_dump()
if temp != myroot:
    print "--- Scanning jukebox directory '%s'" % myroot
    # read jukebox directory and store result to a hash if jukeboxdir
    # does not match the stored version.
    # Read in Jukebox directory, get
    # tree : dictionary with directory : [filenames] mapping
    # playlists : list containing playlist filenames
    # parent: dictionary with directory : parent_dir mapping
    tree, playlists, parent = recurse(myroot, {}, [], {myroot : None})

    # remove dirs containing no music files and invisible dirs from tree dirctionary, get
    # tree : cleaned-up dictionary with directory : [filenames] mapping
    # length : dir : total number of files in subtree
    # playlists : playlists plus memo file
    tree, length, playlists = cleanup(tree, playlists)

    # dump Jukebox data to file (for next start-up)
    dump_data()

# launch web browser unless server-only mode
url = "http://localhost:%s/" % port
if openbrowser:
    print '--- Webserver ready, launching web browser.'
    try:
        webbrowser.open_new(url)
    except:
        print "\n+++ Can not launch web browser, please open URL '%s' manually.\n" % url
else:
    print "\n--- Web server ready, open URL '%s' with your browser.\n" % url

# serve forever...
end_flag = False
while not end_flag or ignore_exit:
    try:
        httpd.handle_request()
    except KeyboardInterrupt:
        print '\n+++ Keyboard interrupt. %s shut down.\n' % progname
        sys.exit(0)
    except:
        print '\n+++ Caught a weird error.'
        httpd.server_close()
        try:
            print '--- Trying to start new server instance ...'
            httpd = BaseHTTPServer.HTTPServer(server_address, moosicWebGUIHTTPRequestHandler)
        except:
            print >> sys.stderr, '\n*** Can not start new server, giving up. Sorry.\n'
            sys.exit(1)

print '\n+++ Caught exit request. %s shut down.\n' % progname

sys.exit(0)

################################################################################
# END
################################################################################