#!/usr/bin/python
# coding=utf-8
from  __future__ import division,unicode_literals,print_function
import os
import commands
import platform
import logging
import sys
import unittest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 命令前缀拼接设置
host_type = platform.platform()
SCRIPTS_NAME=os.basename(os.path.realpath(__file__))

def get_host_ip():
    '''
    shell 中使用下面的python命令可以获取本机IP
    python -c "import socket;print([(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1])"
    :return:
    '''
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

local_host_ip = get_host_ip()

class BaseCheck(object):
    cmd_fail_info = "[%s] 命令未成功执行，命令执行返回状态为[%s]，输出结果为[%s]"

    @staticmethod
    def _runCmd(cmd):
        '''
        执行传入的bash命令
        :param cmd: command
        :return: (status,stdout)
        '''
        return commands.getstatusoutput(cmd)

    def __init__(self,args):
        self.args = args
        self.cmds = {}
        self.outputs = {}

    def gengrateCheckCmd(self):
        pass

    def checkCmdAns(self,output):
        '''
        检查命令执行结果
        :param info: (): arg, cmd_returninfo:(status,output)
        :return:
        '''
        arg, infos = output
        outputInfo = infos[1]
        outputInfo = [info for info in outputInfo.split(os.linesep) if arg in outputInfo]
        self._checkans((arg, outputInfo))

    def _checkans(self,output):
        pass

    def runCmd(self):
        self.gengrateCheckCmd()
        for arg in self.args:
            cmd  = self.cmds.get(arg)
            output = self._runCmd(cmd)
            self.outputs[arg] = output
            status,out = output
            if  status != 0:
                logger.warning(ProgressCheck.cmd_fail_info, cmd, status, out)
            else:
                self.checkCmdAns((arg,output))

class ProgressCheck(BaseCheck):
    def __init__(self,args):
        super(ProgressCheck,self).__init__(args)
        ps_linux_prefix = "ps -ef | grep -v grep | grep -v " + SCRIPTS_NAME +" | grep "
        ps_hpux_prefix = "ps -exf | grep -v grep | grep -v " + SCRIPTS_NAME + " | grep "
        ps_cmd_prefix = {'Linux': ps_linux_prefix,
                         'HP-UX': ps_hpux_prefix,
                         'AIX': ps_linux_prefix}
        self._os_ps_prefix = ps_cmd_prefix.get(host_type, ps_cmd_prefix.get("Linux"))

    def gengrateCheckCmd(self):
        cmd = [self._os_ps_prefix+arg for arg in self.args]
        self.cmds = dict(zip(self.args,cmd))

    def _checkans(self,output):
        app_name, outputInfo = output
        if 1 == len(output):
            logger.info("%s 进程存在.", app_name)
        elif 0 == len(output):
            logger.warning("%s 应用进程不存在!", app_name)
        else:
            logger.info("%s 应用匹配到[%s]个进程,信息如下[%s]",app_name,len(output),output)

class progress_check(unittest.TestCase):
    def setUp(self):
        self.app_name = 'pycharm'
        self.apps = ['cmd', 'dir']


    def test_check_progress(self):

        app_check = ProgressCheck([self.app_name])
        app_check.runCmd()

        app_check = ProgressCheck(self.apps)
        app_check.runCmd()

def main():
    args = sys.argv[1:]
    app_check = ProgressCheck(args)
    app_check.runCmd()

if __name__ == '__main__':
    main()