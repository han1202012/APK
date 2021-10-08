# coding=utf-8
# 导入系统命令
import os


# 对 APK 文件进行批处理
def batch_apk():
    # 列出 apk 目录下的所有文件
    for f in os.listdir('apk'):
        # 文件名长度超过 4 个字符
        if len(f) > 4:
            # 从后面 4 字节到结尾是 .apk ,
            # 则该文件是 APK 文件 , 对该文件进行解包
            if f[-4:] == '.apk':
                os.system('python ApkTool.py -analyse -inapk apk/' + f)


# 主函数入口
if __name__ == '__main__':
    batch_apk()
