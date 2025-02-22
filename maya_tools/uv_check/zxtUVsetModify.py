# -*- coding: utf-8 -*-
import maya.cmds as mc
import maya.mel as mm
import sys
import functools as functools
import time


def getAllGeoNameList():
    """这个返回选择的所有的类型中polyGon名称"""
    mc.select(hi=True)
    get_all_shape = mc.ls(sl=1)
    get_all_GeoName_list = []
    for one_check_mesh in get_all_shape:
        if mc.nodeType(one_check_mesh) == "mesh":
            temp_trans = mc.listRelatives(one_check_mesh, f=True, p=True)
            tmpfindGeo_name = temp_trans[0].split('|')[-1]
            get_all_GeoName_list.append(tmpfindGeo_name)
    return get_all_GeoName_list


def getAllShpNameList():
    """这个返回选择的所有的类型中polyGon_shape的名称"""
    mc.select(hi=True)
    get_all_shape = mc.ls(sl=1)
    get_all_ShpName_list = []
    for one_check_mesh in get_all_shape:
        if mc.nodeType(one_check_mesh) == "mesh":
            get_all_ShpName_list.append(one_check_mesh)

    return get_all_ShpName_list


class zxtUVSetTool:

    def windows_zxtUVSetModify(self):
        if mc.window('zxtUVmodify', ex=1):
            mc.deleteUI('zxtUVmodify', wnd=1)

        mc.window('zxtUVmodify', t='zxtUV_Tool', widthHeight=(250, 250), s=0, resizeToFitChildren=1, mnb=0, mxb=0)
        mc.rowColumnLayout(numberOfColumns=1)

        mc.button(en=0, l='Author:  威武的天哥\nE-mail:  johnny.zxt@gmail.com\nCreated: %s' % time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime()))
        mc.text(label='UV整理的工具v1.5\n ', fn='fixedWidthFont')
        mc.separator(height=5, style='in')
        mc.text(fn="boldLabelFont", label="正确要保留的UV名：")
        mc.textField("the_UV_name", tx='map1')

        mc.separator(height=5, style='in')
        mc.text('')
        mc.separator(height=5, style='in')

        mc.text(fn='boldLabelFont', label='最开始：检查有没有多重UV名称的物体')
        mc.button(l='检查有没有多重UV名称的物体', c='zxtUV.check_multiple_uv_channels()')
        mc.separator(height=5, style='in')
        mc.text(fn='boldLabelFont', label='第一步：检查有没有指定UV名称的物体')
        mc.button(l='检查有没有指定UV名称的物体', c='zxtUV.chkUV()')
        mc.separator(height=5, style='in')
        mc.text(fn='boldLabelFont', label='第二步：重命名当前UV为指定名称')
        mc.button(l='重命名当前UV为指定名称', c='zxtUV.renameUV()')
        mc.separator(height=5, style='in')
        mc.text(fn='boldLabelFont', label='第三步：选择具有指定UV名称以外的物体')
        mc.button(l='选择具有指定UV名称以外的物体', c='zxtUV.selNotSpecificName()')
        mc.separator(height=5, style='in')
        mc.text(fn="boldLabelFont", label="第四步：COPY UV到指定名称下")
        mc.button(l='COPY UV到指定名称下', c='zxtUV.copyUVtoSpecificName()')
        mc.separator(height=5, style='in')
        mc.text(fn="boldLabelFont", label="第五步：删除除指定名称以外的UV")
        mc.button(l='删除指定UV名称以外的UV', c='zxtUV.delUV()')
        mc.separator(height=5, style='in')
        mc.text(fn="boldLabelFont", label="第六步：转换到指定的UV空间")
        mc.button(l='转换到指定的UV空间', c='zxtUV.changeUV()')

        mc.showWindow()

    def ck(self):
        print(getAllGeoNameList())

    def chkUV(self):
        specificUVname = mc.textField("the_UV_name", q=True, tx=True)
        notMapName = []
        for shape in getAllShpNameList():
            uvnames = mc.polyUVSet(shape, q=True, allUVSets=True)
            if specificUVname not in uvnames:
                Tname = mc.listRelatives(shape, p=True)
                notMapName.append(Tname[0])
                print(notMapName)

        if len(notMapName) > 0:
            if_select = mc.confirmDialog(m="场景中有UV名称不为%s的物体，是否要选择这些" % str(specificUVname),
                                         b=['select', 'close'], defaultButton='select', icon='warning')
            if if_select == 'select':
                mc.select(notMapName)

    def selNotSpecificName(self):
        specificUVname = mc.textField("the_UV_name", q=True, tx=True)
        notMapName = []
        for shape in getAllShpNameList():
            uvnames = mc.polyUVSet(shape, q=True, allUVSets=True)
            #print uvnames
            for name in uvnames:
                if name != specificUVname:
                    #mc.polyUVSet(shape,delete=True,uvSet=name)
                    print('%s = %s' % (shape, name))
                    Tname = mc.listRelatives(shape, p=True)
                    #print Tname
                    notMapName.append(Tname[0])
                #print notMapName
        mc.select(notMapName)
        return notMapName

    def copyUVtoSpecificName(self):
        specificUVname = mc.textField("the_UV_name", q=True, tx=True)
        for shape in getAllShpNameList():
            uvnames = mc.polyUVSet(shape, q=True, allUVSets=True)
            for name in uvnames:
                if name != specificUVname:
                    mc.polyCopyUV(shape, uvSetNameInput=name, uvSetName=specificUVname)

    def delUV(self):
        UVname = mc.textField("the_UV_name", q=True, tx=True)
        for shape in getAllShpNameList():
            uvnames = mc.polyUVSet(shape, q=True, allUVSets=True)

            for name in uvnames:
                if name != UVname:
                    mc.polyUVSet(shape, delete=True, uvSet=name)

    def renameUV(self):
        specificUVname = mc.textField("the_UV_name", q=True, tx=True)
        for shape in getAllShpNameList():
            uvnames = mc.polyUVSet(shape, q=True, allUVSets=True)
            if specificUVname != uvnames:
                #get_default_UVname = mc.getAttr('%s.uvSet[0],uvSetName'%shape)

                #currentUVname = mc.polyUVSet(shape,currentUVSet=True,q=True)
                mc.polyUVSet(shape, rename=True, newUVSet=specificUVname, currentUVSet=True)

    def changeUV(self):
        specificUVname = mc.textField("the_UV_name", q=True, tx=True)
        for i in range(len(getAllShpNameList())):
            mc.polyUVSet(getAllShpNameList()[i], currentUVSet=1, uvSet=specificUVname)

    def check_multiple_uv_channels(self):
        """检查场景中的模型是否存在多个 UV 通道"""
        # 获取选中的物体，如果没有选中则检查所有物体
        selection = mc.ls(sl=True, long=True) or []
        if not selection:
            selection = mc.ls(type='mesh', long=True)

        # 存储有多个 UV 通道的物体
        multi_uv_objects = []

        for obj in selection:
            # 如果是 transform 节点，获取其形状节点
            if mc.nodeType(obj) == 'transform':
                shapes = mc.listRelatives(obj, shapes=True, fullPath=True) or []
                if shapes:
                    obj = shapes[0]

            # 检查是否是网格体
            if mc.nodeType(obj) != 'mesh':
                continue
            if mc.getAttr(f"{obj}.intermediateObject"):
                continue

            # 获取 UV 集
            uv_sets = mc.polyUVSet(obj, query=True, allUVSets=True) or []

            # 如果有多个 UV 集，添加到列表
            if len(uv_sets) > 1:
                # 获取物体的 transform 节点
                transform = mc.listRelatives(obj, parent=True, fullPath=True)[0]
                multi_uv_objects.append({
                    'transform': transform,
                    'shape': obj,
                    'uv_sets': uv_sets
                })

        # 显示结果
        if multi_uv_objects:
            result = mc.confirmDialog(
                title='UV 通道检查',
                message=f'发现 {len(multi_uv_objects)} 个物体具有多个 UV 通道\n是否要选中这些物体？',
                button=['选中物体', '显示详细信息', '取消'],
                defaultButton='选中物体',
                cancelButton='取消',
                dismissString='取消'
            )

            if result == '选中物体':
                mc.select([obj['transform'] for obj in multi_uv_objects])
            elif result == '显示详细信息':
                details = '发现以下物体具有多个 UV 通道：\n\n'
                for obj in multi_uv_objects:
                    details += f"物体: {obj['transform']}\n"
                    details += f"UV 通道: {', '.join(obj['uv_sets'])}\n\n"
                mc.confirmDialog(title='详细信息', message=details, button=['确定'])
        else:
            mc.confirmDialog(
                title='UV 通道检查',
                message='所有检查的物体都只有一个 UV 通道',
                button=['确定']
            )

        return multi_uv_objects

    def check_uv_set_names(self):
        """检查场景中所有模型的 UV 集名称"""
        # 获取所有网格体
        all_meshes = mc.ls(type='mesh', long=True)
        non_standard_uvs = []
        specificUVname = mc.textField("the_UV_name", q=True, tx=True)

        # 检查每个网格体的 UV 集
        for mesh in all_meshes:
            uv_sets = mc.polyUVSet(mesh, query=True, allUVSets=True) or []
            if not uv_sets or uv_sets[0] != specificUVname:
                transform = mc.listRelatives(mesh, parent=True, fullPath=True)[0]
                non_standard_uvs.append(transform)

        if non_standard_uvs:
            # 询问用户是否要修改 UV 集名称
            response = mc.confirmDialog(
                title='UV Set 检查',
                message=f'发现 {len(non_standard_uvs)} 个模型的 UV 集名称不是 {specificUVname}\n是否要重命名为 {specificUVname}？',
                button=['重命名', '选择', '取消'],
                defaultButton='选择',
                cancelButton='取消',
                dismissString='取消'
            )

            if response == '重命名':
                for obj in non_standard_uvs:
                    mesh = mc.listRelatives(obj, shapes=True, fullPath=True)[0]
                    current_uvs = mc.polyUVSet(mesh, query=True, allUVSets=True)
                    if current_uvs:
                        try:
                            # 重命名第一个 UV 集为 map1
                            mc.polyUVSet(mesh, rename=True, uvSet=current_uvs[0], newUVSet=specificUVname)
                            # 如果有多个 UV 集，删除其他的
                            for uv_set in current_uvs[1:]:
                                mc.polyUVSet(mesh, delete=True, uvSet=uv_set)
                        except:
                            print(f"无法重命名 {obj} 的 UV 集")
                mc.confirmDialog(message='UV 集重命名完成', button='确定')

            elif response == '选择':
                mc.select(non_standard_uvs)
        else:
            mc.confirmDialog(message=f'所有模型的 UV 集名称都是 {specificUVname}', button='确定')


