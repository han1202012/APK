# coding=utf-8
import os
import sys
import argparse
from subprocess import Popen, PIPE

import sys
reload(sys)
sys.setdefaultencoding('utf8')


class ApkTool:
    def __init__(self, keystore=None, password=None, alias=None):
        if sys.platform == 'win32':
            self.file_separator = '\\'
        else:
            self.file_separator = '/'
        path = ''
        if hasattr(sys, '_MEIPASS'):
            path = sys._MEIPASS + self.file_separator
        self.apktooljar = path + 'apktool.jar'
        self.aapt = path + 'aapt.exe'
        self.objdump_x86 = path + 'objdump_x86.exe'
        self.objdump_arm = path + 'objdump_arm.exe'
        if keystore is None:
            self.keystore = path + 'mykey-123456.keystore'
        else:
            self.keystore = keystore
        if password is None:
            self.password = '123456'
        else:
            self.password = password
        if alias is None:
            self.alias = 'mykey'
        else:
            self.alias = alias
        self.cur_apk = {}
        return

    def unpack(self, apk, path):
        cmd = 'java -jar ' + self.apktooljar + (' d -f -o %s %s' % (path, apk))
        os.system(cmd)
        return

    def pack(self, path, apk):
        cmd = 'java -jar ' + self.apktooljar + (' b %s -o %s' % (path, apk))
        os.system(cmd)
        return

    def sign(self, apk, signed_apk):
        path, file = os.path.split(signed_apk)
        if os.path.exists(path) is False:
            os.makedirs(path)
        keystore = ' -keystore %s -storepass %s' % (self.keystore, self.password)
        signedjar = ' -signedjar %s %s -digestalg SHA1 -sigalg MD5withRSA %s' % (signed_apk, apk, self.alias)
        cmd = 'jarsigner -verbose ' + keystore + signedjar
        print(cmd)
        os.system(cmd)

    def get_apk_label(self, apk_path):
        pipe = Popen([self.aapt, 'dump', 'badging', apk_path], stdout=PIPE)
        if pipe is not None:
            while True:
                line = pipe.stdout.readline()
                line = line.decode('utf-8')
                if len(line) == 0:
                    break
                pos = line.find('application-label:')
                if pos != -1:
                    return line[pos + 19:len(line) - 3]  # \r\n??????2???????????????????????????3?????????
        return ''

    def get_apk_package_name(self, apk):
        pipe = Popen([self.aapt, 'dump', 'badging', apk], stdout=PIPE)
        if pipe is not None:
            while True:
                line = pipe.stdout.readline()
                line = line.decode('utf-8')
                if len(line) == 0:
                    break
                pos = line.find('package:')
                if pos != -1:
                    return line[pos + 8:len(line) - 2]  # \r\n??????2???????????????????????????3?????????
        return ''


def get_game_engine(libpath, file_separator):
    data = {
        'libcocos2dcpp.so': 'cocos?????? cpp',
        'libcocos2dlua.so': 'cocos?????? lua',
        'libcocos2djs.so': 'cocos?????? javascipt',
        'libunity.so': 'unity3D??????',
        'libgdx.so': 'libgdx??????'
    }
    dir = ['armeabi-v7a', 'armeabi', 'x86']
    for d in dir:
        lib = libpath + d + file_separator
        for f in data.keys():
            if os.path.exists(lib + f):
                return data[f]
    return '????????????'


def analyse(apk, tool):
    path, file = os.path.split(apk)
    if len(path) == 0:
        path = '.'
    out_name = file[:-4]
    out_txt = out_name + '.txt'
    f_out = open(out_txt, 'w+')
    line = '???????????????%s\n' % apk
    f_out.write(line)
    line = '???????????????%s\n' % tool.get_apk_label(apk)
    f_out.write(line)
    line = '???????????????%s\n' % tool.get_apk_package_name(apk)
    f_out.write(line)
    unpack_path = path + tool.file_separator + 'unpack' + tool.file_separator + out_name
    if os.path.exists(unpack_path) is False:
        os.makedirs(unpack_path)
    repack_path = path + tool.file_separator + 'repack' + tool.file_separator + out_name + '.apk'
    if os.path.exists(path + tool.file_separator + 'repack') is False:
        os.makedirs(path + tool.file_separator + 'repack')
    sign_path = path + tool.file_separator + 'sign' + tool.file_separator + out_name + '.apk'
    if os.path.exists(path + tool.file_separator + 'sign') is False:
        os.makedirs(path + tool.file_separator + 'sign')
    if os.path.exists(unpack_path + tool.file_separator + 'lib') is False:
        tool.unpack(apk, unpack_path)
    if os.path.exists(repack_path) is False:
        tool.pack(unpack_path, repack_path)
    if os.path.exists(sign_path) is False:
        tool.sign(repack_path, sign_path)
    if os.path.exists(repack_path) is False:
        line = '????????????????????????????????????????????????\n'
    else:
        line = '??????????????????????????????\n'
        is_repack_ok = True
    f_out.write(line)
    if os.path.exists(sign_path) is False:
        line = '????????????????????????????????????????????????\n'
    else:
        line = '??????????????????????????????\n'
    f_out.write(line)
    libpath = unpack_path + tool.file_separator
    libpath += 'lib' + tool.file_separator
    line = '???????????????%s\n' % get_game_engine(libpath, tool.file_separator)
    f_out.write(line)
    f_out.write(
        '----------------------------------------------------------------------------------------------------------------------------------\n')
    f_out.close()
    pass


def main():
    parser = argparse.ArgumentParser(prog=sys.argv[0], usage='%(prog)s [options]')
    help = """help ?????? -h ????????????????????? """
    parser.add_argument('-help', help=help, action='store_const', const='help')
    parser.add_argument('-keystore', nargs='?', help='???????????????????????????mykey-123456.keystore')
    parser.add_argument('-passwd', nargs='?', help='???????????????????????????123456')
    parser.add_argument('-alias', nargs='?', help='???????????????????????????mykey')
    parser.add_argument('-label', help='????????????', action='store_const', const='label')
    parser.add_argument('-unpack', help='????????????', action='store_const', const='unpack')
    parser.add_argument('-pack', help='????????????', action='store_const', const='pack')
    parser.add_argument('-sign', help='????????????', action='store_const', const='sign')
    parser.add_argument('-analyse', help='?????????', action='store_const', const='analyse')
    parser.add_argument('-inapk', nargs='?', help='????????????apk??????')
    parser.add_argument('-outapk', nargs='?', help='????????????apk??????')
    parser.add_argument('-outpath', nargs='?', help='??????????????????')
    parser.add_argument('-inpath', nargs='?', help='??????????????????')
    args = parser.parse_args()
    if args.help is not None:
        parser.print_help()
        return
    attrs = ['keystore', 'passwd', 'alias', 'inapk', 'outapk', 'inpath', 'outpath', 'help']
    value_map = {}
    for attr in attrs:
        value_map[attr] = getattr(args, attr, None)
    tool = ApkTool(value_map['keystore'], value_map['passwd'], value_map['alias'])
    if args.unpack is not None:
        # -unpack -inapk D:\bamenGame\????????????\17.12.18jhzd.apk -outpath D:\bamenGame\????????????\out\17.12.18jhzd
        if value_map['inapk'] is None:
            print('??????????????????apk??????')
            return
        if value_map['outpath'] is None:
            print('????????????????????????')
            return
        tool.unpack(value_map['inapk'], value_map['outpath'])
        return
    if args.pack is not None:
        # -pack -outapk D:\bamenGame\????????????\repack\17.12.18jhzd.apk -inpath D:\bamenGame\????????????\out\17.12.18jhzd
        if value_map['inpath'] is None:
            print('????????????????????????')
            return
        if value_map['outapk'] is None:
            print('???????????????????????????')
            return
        tool.pack(value_map['inpath'], value_map['outapk'])
        return
    if args.sign is not None:
        # -sign -inapk D:\bamenGame\????????????\repack\17.12.18jhzd.apk -outapk D:\bamenGame\????????????\sign\17.12.18jhzd.apk
        if value_map['inapk'] is None:
            print('????????????????????????')
            return
        if value_map['outapk'] is None:
            print('???????????????????????????')
            return
        tool.sign(value_map['inapk'], value_map['outapk'])
        return
    if args.label is not None:
        if value_map['inapk'] is None:
            print('???????????????????????????')
            return
        print(tool.get_apk_label(value_map['inapk']))
        return
    if args.analyse is not None:
        if value_map['inapk'] is None:
            print('??????????????????????????????????????????????????????????????????apk??????')
            for file in os.listdir(os.curdir):
                if os.path.isdir(file):
                    continue
                if os.path.splitext(file)[1] == '.apk':
                    analyse(file, tool)
            return
        analyse(value_map['inapk'], tool)
        return
    parser.print_help()


if __name__ == '__main__':
    main()
