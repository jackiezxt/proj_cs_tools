import maya.cmds as mc
import os
from .utils import handle_error
from .config import CAMERA_SETTINGS, FRAME_RATE
from .render_manager import RenderManager

class CameraManager:
    """相机管理类"""
    @staticmethod
    def find_render_camera():
        """查找并设置渲染相机"""
        cameras = mc.ls(type="camera")
        if not cameras:
            return None, "场景中没有找到相机"
            
        # 先将所有相机设置为不可渲染
        for cam in cameras:
            try:
                mc.setAttr(f"{cam}.renderable", 0)
            except:
                pass
        
        # 按优先级查找相机
        camera_patterns = [
            lambda c: "camera:" in c or "camera|" in c,
            lambda c: "camera" in c.lower(),
            lambda c: True  # 匹配任何相机
        ]
        
        for pattern in camera_patterns:
            for cam in cameras:
                if pattern(cam):
                    try:
                        transform = mc.listRelatives(cam, parent=True)
                        if transform:
                            mc.setAttr(f"{cam}.renderable", 1)
                            return transform[0], None
                    except Exception as e:
                        continue
        
        return None, "未能找到合适的渲染相机"
        
    @staticmethod
    def import_camera(camera_file, status_callback=None):
        """导入相机并设置"""
        try:
            if not os.path.exists(camera_file):
                raise FileNotFoundError(f"相机文件不存在: {camera_file}")
            
            camera_name = os.path.basename(camera_file)
            
            # 导入相机
            mc.file(camera_file, i=True, type="FBX", ignoreVersion=True, 
                   ra=True, mergeNamespacesOnClash=False, namespace=CAMERA_SETTINGS.get("namespace", "camera"))
            
            # 设置帧率
            try:
                mc.currentUnit(time=FRAME_RATE)
            except Exception as e:
                mc.warning(f"设置帧率时出错: {str(e)}，使用默认值")
                mc.currentUnit(time="pal")  # 使用PAL作为默认帧率
            
            # 设置分辨率
            RenderManager.setup_resolution()
            
            # 设置相机
            CameraManager.setup_camera()
            
            # 解析帧范围
            start_frame, end_frame = CameraManager.parse_frame_range(camera_name)
            
            if status_callback:
                status_callback(f"成功导入相机: {camera_name}")
            
            return True, start_frame, end_frame
            
        except Exception as e:
            if status_callback:
                status_callback(f"导入相机时出错: {str(e)}")
            mc.warning(f"导入相机时出错: {str(e)}")
            return False, None, None, str(e)
    
    @staticmethod
    def setup_camera():
        """设置渲染相机"""
        # 先禁用所有相机的渲染
        cameras = mc.ls(type="camera")
        for cam in cameras:
            try:
                mc.setAttr(f"{cam}.renderable", 0)
            except:
                pass
        
        # 查找并设置导入的相机
        for cam in cameras:
            if "camera:" in cam or "camera|" in cam:
                try:
                    mc.setAttr(f"{cam}.renderable", 1)
                    return True
                except:
                    pass
        return False
    
    @staticmethod
    def parse_frame_range(camera_name):
        """从相机文件名解析帧范围"""
        # 安全获取file_prefix，默认为"cam_"
        file_prefix = CAMERA_SETTINGS.get("file_prefix", "cam_").lower()
        
        if not camera_name.lower().startswith(file_prefix):
            return None, None
            
        try:
            parts = camera_name.split('_')
            frame_numbers = []
            
            for part in parts:
                clean_part = part.split('.')[0]
                if clean_part.isdigit():
                    frame_numbers.append(int(clean_part))
            
            if len(frame_numbers) >= 2:
                return frame_numbers[-2], frame_numbers[-1]
            elif frame_numbers:
                return 1, frame_numbers[0]
            
        except:
            pass
        return None, None

    @staticmethod
    def check_camera_exists(namespace="camera"):
        """检查指定命名空间的相机是否已存在"""
        cameras = mc.ls(f"{namespace}:*", type="camera")
        return len(cameras) > 0