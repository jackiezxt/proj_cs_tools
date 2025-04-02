# -*- coding: utf-8 -*-
"""
命令执行模块
提供命令行指令执行和进度报告功能
"""
import os
import subprocess
import threading
import sys
import queue

class CommandExecutor:
    """命令执行器，支持异步执行和进度报告"""
    
    def __init__(self, logger=None):
        """初始化命令执行器"""
        self.logger = logger
        self.process = None
        self.output_queue = queue.Queue()
        self.is_running = False
        self.return_code = None
    
    def execute(self, command, cwd=None, shell=False):
        """同步执行命令
        
        Args:
            command (str or list): 要执行的命令
            cwd (str): 工作目录
            shell (bool): 是否使用shell执行
            
        Returns:
            tuple: (return_code, output)
        """
        try:
            if self.logger:
                self.logger.info(f"执行命令: {command}")
            
            process = subprocess.Popen(
                command,
                cwd=cwd,
                shell=shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            
            output = []
            for line in process.stdout:
                line = line.strip()
                output.append(line)
                if self.logger:
                    self.logger.info(line)
            
            process.wait()
            return process.returncode, "\n".join(output)
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"执行命令时出错: {str(e)}")
            return -1, str(e)
    
    def execute_async(self, command, cwd=None, shell=False, callback=None):
        """异步执行命令
        
        Args:
            command (str or list): 要执行的命令
            cwd (str): 工作目录
            shell (bool): 是否使用shell执行
            callback (callable): 命令完成时的回调函数
            
        Returns:
            bool: 是否成功启动命令
        """
        if self.is_running:
            if self.logger:
                self.logger.warning("已有命令在运行中")
            return False
        
        def read_output(process, queue):
            """读取进程输出并放入队列"""
            for line in iter(process.stdout.readline, ''):
                queue.put(line.strip())
                if self.logger:
                    self.logger.info(line.strip())
            process.stdout.close()
        
        def monitor_process():
            """监控进程，完成后回调"""
            try:
                if self.logger:
                    self.logger.info(f"开始执行命令: {command}")
                
                self.process = subprocess.Popen(
                    command,
                    cwd=cwd,
                    shell=shell,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )
                
                # 启动输出读取线程
                output_thread = threading.Thread(
                    target=read_output,
                    args=(self.process, self.output_queue)
                )
                output_thread.daemon = True
                output_thread.start()
                
                # 等待进程完成
                self.process.wait()
                self.return_code = self.process.returncode
                
                # 等待输出线程完成
                output_thread.join()
                
                if self.logger:
                    self.logger.info(f"命令执行完成，返回码: {self.return_code}")
                
                # 重置状态
                self.is_running = False
                
                # 调用回调函数
                if callback:
                    callback(self.return_code)
                
            except Exception as e:
                if self.logger:
                    self.logger.error(f"监控进程时出错: {str(e)}")
                self.is_running = False
                if callback:
                    callback(-1)
        
        try:
            # 标记为正在运行
            self.is_running = True
            
            # 启动监控线程
            monitor_thread = threading.Thread(target=monitor_process)
            monitor_thread.daemon = True
            monitor_thread.start()
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"启动异步命令时出错: {str(e)}")
            self.is_running = False
            return False
    
    def get_output(self, block=False, timeout=None):
        """获取命令输出
        
        Args:
            block (bool): 是否阻塞等待
            timeout (float): 超时时间(秒)
            
        Returns:
            str or None: 输出行或None
        """
        try:
            return self.output_queue.get(block=block, timeout=timeout)
        except queue.Empty:
            return None
    
    def stop(self):
        """停止正在运行的命令"""
        if not self.is_running or not self.process:
            return
        
        try:
            if self.logger:
                self.logger.info("停止命令执行")
            
            # 终止进程
            self.process.terminate()
            
            # 等待进程终止
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # 如果超时，强制终止
                self.process.kill()
            
            self.is_running = False
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"停止命令时出错: {str(e)}")
    
    def is_running(self):
        """检查命令是否正在运行"""
        return self.is_running 