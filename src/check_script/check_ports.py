#!/usr/bin/python
# coding=utf-8
from __future__ import division,unicode_literals,print_function
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
'''
design concept:
    通过统一的接口进行命令的执行，具体的检查动作，由子类实现。

'''
# common funcation
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
    '''
    run command and check the command output
    '''
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
        '''
        generate shell command
        :return:
        '''
        pass

    def checkCmdAns(self,output):
        '''
        检查命令执行结果
        :param info: (): arg, cmd_returninfo:(status,output)
        :return:
        '''
        arg, infos = output
        outputInfo = infos[1]
        outputInfo = [info for info in outputInfo.split(os.linesep) if port in outputInfo]
        self._checkans((arg,outputInfo))

    def _checkans(self,output):
        '''
        子类要实现的方法
        :param output: (arg,(status,output))
        :return:
        '''
        pass

    def runCmd(self):
        self.gengrateCheckCmd()
        for arg in self.args:
            cmd  = self.cmds.get(arg)
            output = self._runCmd(cmd)
            self.outputs[arg] = output
            status,out = output
            if  status != 0:
                logger.warning(BaseCheck.cmd_fail_info, cmd, status, out)
            else:
                self.checkCmdAns((arg,output))

class PortsCheck(BaseCheck):
    global local_host_ip
    normal_info = "[%s] 端口存在"
    abnormal_info = "[%s] 端口不存在"
    third_part_info = "[%s] 端口查询信息如下: [%s]"
    # 0.0.0.0:port,:::port,*.port,IP.port,127.0.0.1:port格式表示正常
    port_listen_info=[
        '0.0.0.0:%s',
        '*:%s',
        ':::%s',
        '127.0.0.1:%s',
        local_host_ip+":%s"
    ]

    def __init__(self,args):
        super(PortsCheck, self).__init__(args)
        common_prefix = 'netstat -an | grep -v grep |grep python| grep {}'
        port_cmd_prefix = {'Linux': common_prefix,
                         'HP-UX': common_prefix,
                         'AIX': common_prefix}
        self._os_port_prefix = port_cmd_prefix.get(host_type, port_cmd_prefix.get("Linux"))

    def gengrateCheckCmd(self):
        cmd = [self._os_port_prefix.format(arg) for arg in self.args]
        self.cmds = dict(zip(self.args,cmd))

    def _checkans(self,output):
        port, outputInfo = output
        if 0 == len(output):
            logger.warning(PortsCheck.abnormal_info, port)
        else:
            port_listen_str = [info.format(port) for info in PortsCheck.port_listen_info]
            is_normal = False
            for str in port_listen_str:
                for info in outputInfo:
                    if str in info:
                        is_normal = True
                        break
            if is_normal:
                logger.info(PortsCheck.normal_info,port)
            else:
                logger.info(PortsCheck.third_part_info,port,str(outputInfo))

class port_check(unittest.TestCase):
    def setUp(self):
        self.app_name = 'pycharm'
        self.apps = ['cmd', 'dir']


    def test_check_progress(self):

        app_check = PortsCheck([self.app_name])
        app_check.runCmd()

        app_check = PortsCheck(self.apps)
        app_check.runCmd()

        print (local_host_ip)

def main():
    args = sys.argv[1:]
    app_check = PortsCheck(args)
    app_check.runCmd()

if __name__ == '__main__':
    main()