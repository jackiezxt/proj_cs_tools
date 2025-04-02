#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Maya Virus Scanner and Cleaner - Main Entry
"""

import os
import sys
import argparse
import traceback
import datetime

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 检测Python版本
PY3 = sys.version_info[0] == 3

# Set up global exception handler
def global_exception_handler(exc_type, exc_value, exc_tb):
    """Global exception handler"""
    print("\n======= ERROR =======")
    print("Error type: {}".format(exc_type.__name__))  # 兼容Python 2和3的格式化
    print("Error message: {}".format(exc_value))
    print("\nStack trace:")
    traceback.print_tb(exc_tb)
    print("\nPlease report this error.")
    print("=====================\n")
    
    # Wait for user input
    if os.name == 'nt':  # Windows
        os.system('pause')

# Set the global exception handler
sys.excepthook = global_exception_handler

try:
    # Import custom modules
    from core.scanner import VirusScanner
    from core.cleaner import VirusCleaner
    from utils.logger import Logger
    
    # Try to import Qt modules - 支持多种Qt绑定
    QT_AVAILABLE = False
    
    # 首先尝试PySide2 (Maya 2020-2023)
    try:
        from PySide2 import QtWidgets
        from ui.main_window import MainWindow
        QT_AVAILABLE = True
        print("Using PySide2 for UI")
    except ImportError:
        # 尝试PySide6 (Maya 2024+)
        try:
            from PySide6 import QtWidgets
            from ui.main_window import MainWindow
            QT_AVAILABLE = True
            print("Using PySide6 for UI")
        except ImportError:
            # 最后尝试PyQt5作为备选
            try:
                from PyQt5 import QtWidgets
                from ui.main_window import MainWindow
                QT_AVAILABLE = True
                print("Using PyQt5 for UI")
            except ImportError as e:
                print("Warning: Cannot import Qt modules, error: {}".format(str(e)))
                print("GUI mode will not be available, but command line mode will still work.")
                
except ImportError as e:
    print("Error: Failed to import modules, error: {}".format(str(e)))
    print("Please check if the program is installed correctly.")
    if os.name == 'nt':  # Windows
        os.system('pause')
    sys.exit(1)

def run_cli(args):
    """Run command-line interface"""
    try:
        # Set up logging
        log_dir = os.path.join(os.path.dirname(__file__), "logs")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = os.path.join(log_dir, "scan_{}.log".format(timestamp))  # 兼容Python 2和3的格式化
        
        # Create logger
        logger = Logger(log_path)
        logger.info("Starting Maya Virus Scanner - CLI Mode")
        
        # Execute operations based on arguments
        if args.scan_startup_scripts:
            logger.info("Scanning startup scripts")
            scanner = VirusScanner(log_path)
            results = scanner.scan_system_startup_scripts()
            
            # Show results
            infected_count = len(results.get("infected_files", []))
            logger.info("Scan complete, found {} suspicious files".format(infected_count))
            
            # Clean if needed
            if args.clean and infected_count > 0:
                logger.info("Cleaning startup scripts")
                cleaner = VirusCleaner(log_path)
                cleaner.clean_system_startup_scripts()
                logger.info("Cleaning complete")
        
        elif args.path:
            # Scan file or directory
            path = args.path
            if not os.path.exists(path):
                logger.error("Path does not exist: {}".format(path))
                return 1
            
            scanner = VirusScanner(log_path)
            
            if os.path.isdir(path):
                # Scan directory
                logger.info("Scanning directory: {}".format(path))
                results = scanner.scan_folder(path, recursive=args.recursive)
                
                # Show results
                scanned = results.get("files_scanned", 0)
                infected = results.get("files_infected", 0)
                logger.info("Scan complete, scanned {} files, found {} infected files".format(scanned, infected))
                
                # Clean if needed
                if args.clean and infected > 0:
                    logger.info("Starting to clean infected files")
                    cleaner = VirusCleaner(log_path)
                    
                    for file_info in results.get("infected_files", []):
                        file_path = file_info.get("file")
                        if file_path and file_path.lower().endswith('.ma'):
                            logger.info("Cleaning file: {}".format(file_path))
                            cleaner.clean_file(file_path, make_backup=args.backup)
                    
                    logger.info("Cleaning complete")
            
            else:
                # Scan single file
                logger.info("Scanning file: {}".format(path))
                results = scanner.scan_file(path)
                
                # Show results
                infected = results and results["summary"].get("infected", False)
                status = 'infected' if infected else 'clean'
                logger.info("Scan complete, file is {}".format(status))
                
                # Clean if needed
                if args.clean and infected:
                    logger.info("Starting to clean file")
                    cleaner = VirusCleaner(log_path)
                    cleaner.clean_file(path, make_backup=args.backup)
                    logger.info("Cleaning complete")
        
        else:
            logger.error("No operation specified, use --path or --scan-startup-scripts")
            return 1
        
        logger.info("Program execution complete")
        return 0
    
    except Exception as e:
        print("Error during execution: {}".format(str(e)))
        traceback.print_exc()
        return 1

def run_gui():
    """Run graphical interface"""
    try:
        # 确保在正确版本的Qt下导入UI模块
        if not QT_AVAILABLE:
            print("GUI mode is not available because Qt modules could not be imported.")
            print("Please install PySide2, PySide6, or PyQt5.")
            return 1
            
        # 直接使用MainWindow类创建窗口
        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
        window = MainWindow()
        window.show()
        return app.exec_()
    
    except Exception as e:
        print("Error starting GUI: {}".format(str(e)))
        traceback.print_exc()
        return 1

def main():
    """Main function, handle command line arguments"""
    parser = argparse.ArgumentParser(description="Maya Virus Scanner and Cleaner")
    
    # Add command line arguments
    parser.add_argument("--path", help="Path to file or folder to scan")
    parser.add_argument("--recursive", action="store_true", help="Scan subfolders recursively")
    parser.add_argument("--scan-startup-scripts", action="store_true", help="Scan system startup scripts")
    parser.add_argument("--clean", action="store_true", help="Clean found viruses")
    parser.add_argument("--backup", action="store_true", help="Create backup before cleaning")
    parser.add_argument("--gui", action="store_true", help="Start graphical interface")
    
    # Parse command line arguments
    args = parser.parse_args()
    
    # Run GUI or CLI
    if args.gui or not (args.path or args.scan_startup_scripts):
        return run_gui()
    else:
        return run_cli(args)

if __name__ == "__main__":
    sys.exit(main()) 