# coding=utf-8
import os
import sys
import argparse
from subprocess import Popen, PIPE


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
                    return line[pos + 19:len(line) - 3]  # \r\n占了2个，加上单引号一共3个字符
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
                    return line[pos + 8:len(line) - 2]  # \r\n占了2个，加上单引号一共3个字符
        return ''


def get_game_engine(libpath, file_separator):
    data = {
        'libcocos2dcpp.so': 'cocos引擎 cpp',
        'libcocos2dlua.so': 'cocos引擎 lua',
        'libcocos2djs.so': 'cocos引擎 javascipt',
        'libunity.so': 'unity3D引擎',
        'libgdx.so': 'libgdx引擎'
    }
    dir = ['armeabi-v7a', 'armeabi', 'x86']
    for d in dir:
        lib = libpath + d + file_separator
        for f in data.keys():
            if os.path.exists(lib + f):
                return data[f]
    return '未知引擎'


def analyse(apk, tool):
    path, file = os.path.split(apk)
    if len(path) == 0:
        path = '.'
    out_name = file[:-4]
    out_txt = out_name + '.txt'
    f_out = open(out_txt, 'w+')
    line = '文件名称：%s\n' % apk
    f_out.write(line)
    line = '应用名称：%s\n' % tool.get_apk_label(apk)
    f_out.write(line)
    line = '应用信息：%s\n' % tool.get_apk_package_name(apk)
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
        line = '打包检测：重打包失败，无法重打包\n'
    else:
        line = '打包检测：重打包成功\n'
        is_repack_ok = True
    f_out.write(line)
    if os.path.exists(sign_path) is False:
        line = '签名检测：重签名失败，无法重签名\n'
    else:
        line = '签名检测：重签名成功\n'
    f_out.write(line)
    libpath = unpack_path + tool.file_separator
    libpath += 'lib' + tool.file_separator
    line = '引擎检测：%s\n' % get_game_engine(libpath, tool.file_separator)
    f_out.write(line)
    f_out.write(
        '----------------------------------------------------------------------------------------------------------------------------------\n')
    f_out.close()
    pass


def main():
    parser = argparse.ArgumentParser(prog=sys.argv[0], usage='%(prog)s [options]')
    help = """help 或者 -h 显示本帮助文档 """
    parser.add_argument('-help', help=help, action='store_const', const='help')
    parser.add_argument('-keystore', nargs='?', help='指定签名文件，默认mykey-123456.keystore')
    parser.add_argument('-passwd', nargs='?', help='指定签名密码，默认123456')
    parser.add_argument('-alias', nargs='?', help='指定签名别名，默认mykey')
    parser.add_argument('-label', help='获取包名', action='store_const', const='label')
    parser.add_argument('-unpack', help='解包文件', action='store_const', const='unpack')
    parser.add_argument('-pack', help='打包文件', action='store_const', const='pack')
    parser.add_argument('-sign', help='签名文件', action='store_const', const='sign')
    parser.add_argument('-analyse', help='分析包', action='store_const', const='analyse')
    parser.add_argument('-inapk', nargs='?', help='指定输入apk路径')
    parser.add_argument('-outapk', nargs='?', help='指定输出apk路径')
    parser.add_argument('-outpath', nargs='?', help='指定输出目录')
    parser.add_argument('-inpath', nargs='?', help='指定输入目录')
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
        # -unpack -inapk D:\bamenGame\测试游戏\17.12.18jhzd.apk -outpath D:\bamenGame\测试游戏\out\17.12.18jhzd
        if value_map['inapk'] is None:
            print('需要指定输入apk路径')
            return
        if value_map['outpath'] is None:
            print('需要指定输出目录')
            return
        tool.unpack(value_map['inapk'], value_map['outpath'])
        return
    if args.pack is not None:
        # -pack -outapk D:\bamenGame\测试游戏\repack\17.12.18jhzd.apk -inpath D:\bamenGame\测试游戏\out\17.12.18jhzd
        if value_map['inpath'] is None:
            print('需要指定输入目录')
            return
        if value_map['outapk'] is None:
            print('需要指定输出包路径')
            return
        tool.pack(value_map['inpath'], value_map['outapk'])
        return
    if args.sign is not None:
        # -sign -inapk D:\bamenGame\测试游戏\repack\17.12.18jhzd.apk -outapk D:\bamenGame\测试游戏\sign\17.12.18jhzd.apk
        if value_map['inapk'] is None:
            print('需要指定输入目录')
            return
        if value_map['outapk'] is None:
            print('需要指定输出包路径')
            return
        tool.sign(value_map['inapk'], value_map['outapk'])
        return
    if args.label is not None:
        if value_map['inapk'] is None:
            print('需要指定输入游戏包')
            return
        print(tool.get_apk_label(value_map['inapk']))
        return
    if args.analyse is not None:
        if value_map['inapk'] is None:
            print('需要指定输入游戏包，现在分析当前目录下所有的apk文件')
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
