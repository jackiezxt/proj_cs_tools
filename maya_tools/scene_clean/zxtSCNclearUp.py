#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
  Author:  johnnyzxt
  E-mail:  johnny.zxt@gmail.com
  Created: 2016/7/28 19:18:47
  Description:
  用于复制物体A到指定位置
  Instruction:

"""
import maya.cmds as mc
import maya.mel as mm
import sys
import functools as functools
import time
import os

if mc.window('zxtDupToPos', ex=1):
    mc.deleteUI('zxtDupToPos', wnd=1)


def dup_to_pos(arg):
    sel = mc.ls(sl=1)
    trans = sca = rot = 0
    for i in sel[1:len(sel)]:
        dup = mc.duplicate(sel[0])
        trans = mc.xform(i, q=1, rp=1, ws=1)
        sca = mc.xform(i, q=1, s=1)
        rot = mc.xform(i, q=1, ro=1, os=1)
        print('%s.translation=%s' % (i, trans))
        print('%s.scale=%s' % (i, sca))
        print('%s.rot=%s' % (i, rot))
        mc.move(trans[0], trans[1], trans[2], dup, a=1, ws=1, rpr=1)
        mc.xform(dup, t=trans, s=sca, ro=rot)
    mc.delete(sel[0])


def instance_to_pos(arg):
    sel = mc.ls(sl=1)
    trans = sca = rot = 0
    for i in sel[1:len(sel)]:
        dup = mc.instance(sel[0])
        trans = mc.xform(i, q=1, rp=1, ws=1)
        sca = mc.xform(i, q=1, s=1)
        rot = mc.xform(i, q=1, ro=1, os=1)
        print('%s.translation=%s' % (i, trans))
        print('%s.scale=%s' % (i, sca))
        print('%s.rot=%s' % (i, rot))
        mc.move(trans[0], trans[1], trans[2], dup, a=1, ws=1, rpr=1)
        mc.xform(dup, t=trans, s=sca, ro=rot)
    mc.delete(sel[0])


def transform_to_pos(arg):
    sel = mc.ls(sl=1)
    trans = sca = rot = 0
    for i in sel[1:len(sel)]:
        dup = sel[0]
        trans = mc.xform(i, q=1, rp=1, ws=1)
        sca = mc.xform(i, q=1, s=1)
        rot = mc.xform(i, q=1, ro=1, os=1)
        print('%s.translation=%s' % (i, trans))
        print('%s.scale=%s' % (i, sca))
        print('%s.rot=%s' % (i, rot))
        mc.move(trans[0], trans[1], trans[2], dup, a=1, ws=1, rpr=1)
        mc.xform(dup, t=trans, s=sca, ro=rot)
    # mc.delete(sel[0])


def del_pasted_name(arg):
    try:
        objects = mc.ls('pasted__*')
        mc.select(objects, noExpand=True)
    except:
        mc.confirmDialog(m=u'没有pasted__名称的节点', b='close')
    else:
        sel = mc.ls(sl=1)
        for j in range(len(sel)):
            getsel = sel[j]
            f = getsel.replace('pasted__', '')
            try:
                renamedShp = mc.rename(sel[j], f)
            except:
                print('The polygon %s and the shape had been renamed to %s.' % (sel[j], renamedShp))
            else:
                seltyp = mc.nodeType(renamedShp)
                if seltyp != 'transform' and 'mesh':
                    print('The %s node %s has been renamed to %s' % (seltyp, sel[j], renamedShp))


def del_multi_shapes(self):
    selTrans = mc.ls(typ="transform")
    errorTransContainer = []
    for transName in selTrans:
        shapes = mc.listRelatives(transName, s=1)
        if shapes:  # 排除shapes有none的type
            if len(shapes) > 1:  # 排除shapes只有一个的正常模型
                errorTransContainer.append(transName)

    if errorTransContainer:
        if_delete = mc.confirmDialog(
            m=u'%s \n 这些模型名称具有多个shape节点，是要删除他们？还是选择他们？' % [str(r) for r in errorTransContainer],
            button=['delete', 'select'], defaultButton='select', icon='warning')
        if if_delete == 'delete':
            for transName in selTrans:
                shapes = mc.listRelatives(transName, s=1)
                if shapes:
                    if len(shapes) > 1:
                        print(u'%s 已经被删除' % shapes[1])
                        mc.delete(shapes[1])
        if if_delete == 'select':
            mc.select(errorTransContainer)
    else:
        mc.confirmDialog(m=u'场景中没有多余的shape', b='Close')  #


def del_turtle_render(arg):
    if mc.objExists('TurtleRenderOptions'):
        mc.lockNode('TurtleRenderOptions', 'TurtleUIOptions', 'TurtleBakeLayerManager', 'TurtleDefaultBakeLayer',
                    lock=0)
        mc.delete('TurtleRenderOptions', 'TurtleUIOptions',
                  'TurtleBakeLayerManager', 'TurtleDefaultBakeLayer')
        mc.confirmDialog(m=u'海龟节点的垃圾已经被清除', b='close')
    else:
        mc.confirmDialog(m=u'场景中没有海龟渲染器的残留', b='close')


def del_renderman(arg):
    mm.eval('rmanPurgePlugin;')


def init_vr_renderer(arg):
    mc.setAttr('vraySettings.rtv_SRGB', 0)
    mc.setAttr('vraySettings.giOn', 1)
    mc.setAttr('vraySettings.cmap_adaptationOnly', 2)
    mc.setAttr('vraySettings.imageFormatStr',
               'exr (multichannel)', type='string')
    mc.setAttr('vraySettings.refractiveCaustics', 0)
    mc.setAttr('vraySettings.dmcs_timeDependent', 0)
    mc.setAttr('vraySettings.sys_embreeUse', 1)
    mc.setAttr('vraySettings.dmc_subdivs', 32)
    mc.setAttr('vraySettings.globopt_render_viewport_subdivision', 1)
    mc.setAttr('vraySettings.fileNamePrefix',
               '<Scene>/<Layer>/<Layer>', type='string')
    mc.setAttr('vraySettings.cam_overrideEnvtex', 1)
    mc.setAttr('vraySettings.cam_envtexGi', 0.0672,
               0.0681439, 0.084, type='double3')


def add_aov_vr(arg):
    mm.eval('vrayAddRenderElement    LightSelectElement;\
    setAttr "vrayRE_Light_Select.vray_type_lightselect" 2;\
    vrayAddRenderElement    LightSelectElement;\
    setAttr "vrayRE_Light_Select1.vray_type_lightselect" 2;\
    vrayAddRenderElement    LightSelectElement;\
    setAttr "vrayRE_Light_Select2.vray_type_lightselect" 2;\
    vrayAddRenderElement    giChannel;\
    vrayAddRenderElement    reflectChannel;\
    vrayAddRenderElement    FastSSS2Channel;\
    vrayAddRenderElement    specularChannel;\
    vrayAddRenderElement    velocityChannel;\
    vrayAddRenderElement    zdepthChannel;\
    vrayAddRenderElement    MultiMatteElement;\
    setAttr "vrayRE_Multi_Matte.vray_redid_multimatte" 1;\
    setAttr "vrayRE_Multi_Matte.vray_greenid_multimatte" 2;\
    setAttr "vrayRE_Multi_Matte.vray_blueid_multimatte" 3;')


def build_subdive(arg):
    mm.eval('$meshName = `ls -sl`;\
    $shape = `listRelatives -f -s $meshName`;\
    for ($s = 0; $s < size($shape); ++$s)\
    {\
        vray   addAttributesFromGroup $shape[$s]   "vray_subdivision" 1;\
        vray   addAttributesFromGroup $shape[$s]   "vray_subquality"  1;\
        setAttr ($shape[$s] + ".vrayEdgeLength") 1.5;\
    }')


def dele_subdive(arg):
    mm.eval('$meshName = `ls -sl`;\
    $shape = `listRelatives -f -s $meshName`;\
    for ($s = 0; $s < size($shape); ++$s)\
    {\
        vray   addAttributesFromGroup $shape[$s]   "vray_subdivision" 0;\
        vray   addAttributesFromGroup $shape[$s]   "vray_subquality"  0;\
    }')


def set_sub_value(arg1, arg2):
    meshName = mc.ls(sl=1)
    shapes = mc.listRelatives(meshName, f=1, s=1)
    EdgeLengthValue = mc.floatSliderGrp(arg1, q=1, v=1)
    MaxSubdiveValue = mc.intSliderGrp(arg2, q=1, v=1)
    for i in range(len(shapes)):
        mc.setAttr('%s.vrayEdgeLength' % shapes[i], EdgeLengthValue)
        mc.setAttr('%s.vrayMaxSubdivs' % shapes[i], MaxSubdiveValue)


def build_subdive_win_ui(arg):
    meshName = mc.ls(sl=1)
    shapes = mc.listRelatives(meshName, f=1, s=1)
    if mc.window('zxtBuildSub', ex=1):
        mc.deleteUI('zxtBuildSub', wnd=1)
    mc.window('zxtBuildSub', t=u'Vray批量添加细分', widthHeight=(
        250, 250), s=0, resizeToFitChildren=1, mnb=0, mxb=0)
    mc.columnLayout(adj=1)
    mc.text(label=u'先在视图窗口中框选要添加属性的polygon模型')
    mc.separator(height=5, style='in')
    mc.button(label=u'添加细分属性', c=build_subdive)
    mc.button(label=u'删除细分属性', c=dele_subdive)
    subdieveSlider1 = mc.floatSliderGrp(label='Edge Length', field=True, fieldMinValue=0, fieldMaxValue=20, minValue=0,
                                        maxValue=20, value=0)
    subdieveSlider2 = mc.intSliderGrp(label='Max subdivs', field=True, fieldMinValue=4, fieldMaxValue=512, minValue=4,
                                      maxValue=512, value=4)
    mc.button(label=u'修改细分属性', c=lambda x: set_sub_value(
        subdieveSlider1, subdieveSlider2))

    mc.showWindow()


def clean_plugins(self):
    unknowPluginsList = mc.unknownPlugin(list=True, q=True)
    # unknowPluginStr =  ','.join(unknowPluginsList)
    if unknowPluginsList:
        for unPlugin in unknowPluginsList:
            print(unPlugin)
            try:
                mc.unknownPlugin(unPlugin, remove=True)
            except RuntimeError:
                print(u"%s这个插件不能被清理，因为它还在被其它节点使用" % unPlugin)
        print(u'%s \n 这些插件信息已被清理' % [str(r) for r in unknowPluginsList])
        mc.confirmDialog(m='%s \n 这些插件信息已被清理' %
                           [str(r) for r in unknowPluginsList], b='close')
    else:
        mc.confirmDialog(m=u'场景中不存在垃圾插件信息', b='close')


def clean_virus(self):
    """清理所有已知病毒"""
    # 要清理的文件列表
    virus_files = [
        'vaccine.py', 'vaccine.pyc',
        'userSetup.py', 'userSetup.pyc',
        'fuckVirus.py', 'fuckVirus.pyc'
    ]

    # 要清理的节点前缀
    virus_prefixes = ['vacc', 'breed', 'fuckVirus', 'vaccine_gene', 'breed_gene']

    # 清理文件
    scripts_dir = mc.internalVar(userAppDir=True) + 'scripts'
    for file in virus_files:
        file_path = os.path.join(scripts_dir, file)
        if os.path.exists(file_path):
            os.remove(file_path)

    # 清理节点
    for sel in mc.ls(type='script'):
        if any(sel.startswith(prefix) for prefix in virus_prefixes):
            try:
                mc.setAttr('%s.scriptType' % sel, 0)
                mc.delete(sel)
                print('已删除: %s' % sel)
            except:
                print('无法删除: %s' % sel)

    # 清理scriptJob
    for job in mc.scriptJob(listJobs=True):
        if "leukocyte.antivirus" in job:
            num = int(job.split(":")[0])
            mc.scriptJob(kill=num, force=True)


def clean_on_model_change3dc(self):
    import pymel.core as pm

    # Get all model editors in Maya and reset the editorChanged event
    for item in pm.lsUI(editors=True):
        if isinstance(item, pm.ui.ModelEditor):
            pm.modelEditor(item, edit=True, editorChanged="")
    mc.confirmDialog(m=u'已全部重置编辑器', b='close')


def find_scriptNodes(self):
    """
    Find the all the scriptNode in the scene
    :return: list of script nodes
    """
    mayafile_scriptNodes = []
    for script in mc.ls(type='script'):
        mayafile_scriptNodes.append(script)
    return mayafile_scriptNodes


def renderLayerBugFix(self):
    mm.eval("fixRenderLayerOutAdjustmentErrors")


def clean_unknown_nodes(self):
    """清理所有类型的未知节点"""
    unknown_types = ['unknown', 'unknownDag', 'unknownTransform']
    cleaned_nodes = []

    # 获取所有未知节点
    unknown_nodes = mc.ls(type=unknown_types)
    if unknown_nodes:
        for node in unknown_nodes:
            try:
                mc.lockNode(node, l=0)
                mc.delete(node)
                cleaned_nodes.append(node)
            except:
                print(u'无法删除节点: %s' % node)

    if cleaned_nodes:
        mc.confirmDialog(m=u'已清理以下未知节点:\n%s' % '\n'.join(cleaned_nodes), b='close')
    else:
        mc.confirmDialog(m=u'场景中不存在未知节点', b='close')


def chkShadToFace(self):
    allGeoShp = mc.ls(type='mesh')
    faceGeoShp = []
    for selGeoShp in allGeoShp:
        shadingEngine = mc.listConnections(selGeoShp, t="shadingEngine")
        if shadingEngine:
            if len(shadingEngine) > 1:
                mc.select(selGeoShp, add=1)
                faceGeoShp.append(selGeoShp)
    if not faceGeoShp:
        mc.confirmDialog(m=u'场景中没有按面给予的材质', b='Close')


def renameShader(self):
    '根据模型命名重命名所有的shader'
    allGeoShp = mc.ls(type='mesh')
    for selGeoShp in allGeoShp:
        baseModName = mc.listRelatives(selGeoShp, parent=True, fullPath=True)
        shadingEngine = mc.listConnections(selGeoShp, t='shadingEngine')
        if shadingEngine:
            oldShdName = mc.listConnections(
                shadingEngine, source=True, destination=False, shapes=True)
        preFixName = mc.textFieldButtonGrp(
            'renameShaderPrefix', q=True, text=True)
        if selGeoShp == oldShdName[1]:
            print(oldShdName[0], (preFixName + baseModName[0]))
            try:
                mc.rename(oldShdName[0], preFixName + baseModName[0])
            except:
                print('%s is still using "lambert1", PLEASE Change IT !!!!!!!!!!!!' % baseModName[0])


def removeRogueModelPanelChangeEvents():
    EVIL_METHOD_NAMES = ['DCF_updateViewportList', 'CgAbBlastPanelOptChangeCallback']
    capitalEvilMethodNames = [name.upper() for name in EVIL_METHOD_NAMES]
    modelPanelLabel = mm.eval('localizedPanelLabel("ModelPanel")')
    processedPanelNames = []
    panelName = mc.sceneUIReplacement(getNextPanel=('modelPanel', modelPanelLabel))
    while panelName and panelName not in processedPanelNames:
        editorChangedValue = mc.modelEditor(panelName, query=True, editorChanged=True)
        parts = editorChangedValue.split(';')
        newParts = []
        changed = False
        for part in parts:
            for evilMethodName in capitalEvilMethodNames:
                if evilMethodName in part.upper():
                    changed = True
                    break
            else:
                newParts.append(part)
        if changed:
            mc.modelEditor(panelName, edit=True, editorChanged=';'.join(newParts))
        processedPanelNames.append(panelName)
        panelName = mc.sceneUIReplacement(getNextPanel=('modelPanel', modelPanelLabel))


def clearCGABError(self):
    removeRogueModelPanelChangeEvents()
    mc.confirmDialog(m=u'已清除CgAbBlastPanelOptChangeCallback的报错', b='close')


def clearEmptyTransform(self):
    selTrans = mc.ls(typ='transform')
    transContainer = []
    for transName in selTrans:
        shpContainer = mc.listRelatives(transName)

        if not shpContainer:
            print('%s = %s' % (transName, shpContainer))
            mc.delete(transName)
            transContainer.append(transName)
    if not transContainer:
        mc.confirmDialog(m=u'场景中不存在空组和空物体', b='close')


def clearIntermediateObj(self):
    selShp = mc.ls(typ='mesh')
    interTransContainer = []
    interShpContainer = []
    # selectOneTrans = []
    for shpName in selShp:
        interAttr = mc.getAttr('%s.intermediateObject' % shpName)
        if interAttr == 1:
            selectOneTransName = mc.listRelatives(shpName, ap=True)
            interTransContainer.append(selectOneTransName[0])
            interShpContainer.append(shpName)
            print('%s ===> %s' % (selectOneTransName[0], shpName))
            # mc.select(shpName, add=1)
            # mc.delete(shpName)
            # print( shpName)

    if interTransContainer:
        if_delete = mc.confirmDialog(
            m=u'\n\r场景中这些物件存在隐藏的多个shape节点，删除他们的隐藏shape？？？还是选中他们？？？', button=[
                'delete', 'select'], defaultButton='select', icon='warning')
        if if_delete == 'delete':
            mc.delete(interShpContainer)
        if if_delete == 'select':
            mc.select(interTransContainer)

    if not interTransContainer:
        mc.confirmDialog(m=u'场景中不存在intermediate的shape节点', b='close')


def clearMSRenderMan(self):
    sel = mc.ls('Pxr*')
    sel.append('Omni*')
    for i in sel:
        mc.lockNode(i, l=0)
        mc.delete(i)


def clearMSRenderGloble(self):
    attr_name = ''
    renderGlobals_prams_list = ['pram', 'poam', 'prlm', 'polm', 'prm', 'pom']
    for i in renderGlobals_prams_list:
        attr_name = 'defaultRenderGlobals.%s' % i
        if len(attr_name) > 0:
            mc.setAttr(attr_name, '', type='string')


def renameRSAOVprefix(self):
    rsAOVname = mc.ls(type='RedshiftAOV')
    rsAOVprefixname = mc.textField('RS_AOV_namePrefix', q=True, text=True)
    for aovName in rsAOVname:
        mc.setAttr('%s.filePrefix' % aovName, rsAOVprefixname, type='string')


def unlockInit():
    """Unlock initial Maya nodes that are commonly locked
    """
    lock_lst = ['initialParticleSE', 'renderPartition', 'initialShadingGroup', 'defaultTextureList1']
    for node in lock_lst:
        try:
            mc.lockNode(node, l=0, lu=0)
            print('Successfully unlocked: {}'.format(node))
        except Exception as e:
            print('Failed to unlock {}: {}'.format(node, str(e)))


def optimize_scene(self):
    """解决outline报错， 解决视窗报错"""
    # 优化outliner
    try:
        for x in mc.lsUI(panels=1):
            if mc.objectTypeUI(x) == "ToutlinerEditor":
                # cmds.outlinerEditor(x, e=1, selectCommand="pass")
                mm.eval('outlinerEditor -edit -selectCommand "" "%s";' % x)
    except:
        pass

    # 优化modelEditor
    try:
        for x in mc.lsUI(editors=1):
            if mc.objectTypeUI(x) == "modelEditor":
                mc.modelEditor(x, e=1, editorChanged="")
    except:
        pass

    # 清楚未加载插件
    try:
        unknown_list = mc.ls(type='unknown')
        if unknown_list:
            for i in unknown_list:
                if mc.objExists(i):
                    mc.lockNode(i, l=0)
                    mc.delete(i)
        plug_list = mc.unknownPlugin(q=True, l=True)
        if plug_list:
            for i in plug_list:
                try:
                    mc.unknownPlugin(i, r=1)
                except:
                    pass
        print("clear success!")
    except:
        pass

    # 清楚shapes工具节点
    shapes_node = r"defaultLegacyAssetGlobals"
    if mc.objExists(shapes_node):
        try:
            mc.lockNode(shapes_node, l=0)
            mc.delete(shapes_node)
        except:
            pass

    # 优化拷贝动画
    try:
        for model_panel in mc.getPanel(typ="modelPanel"):
            # Get callback of the model editor
            callback = mc.modelEditor(model_panel, query=True, editorChanged=True)

            # If the callback is the erroneous `CgAbBlastPanelOptChangeCallback`
            if callback == "CgAbBlastPanelOptChangeCallback":
                # Remove the callbacks from the editor
                mc.modelEditor(model_panel, edit=True, editorChanged="")
    except:
        pass

    # 删除所有 script 节点
    del_all_script()
    unlockInit()

    # 默认材质球 add by zzj
    try:
        mc.setAttr("initialShadingGroup.ro", True)
    except:
        pass


def optimize_UVmode(self):
    for x in mc.ls(type="file"):
        uvmode = mc.getAttr(x + ".uvTilingMode")
        image_path = mc.getAttr(x + ".fileTextureName")
        image_path_short = os.path.split(image_path)[1]

        mc.setAttr(x + ".cs", "sRGB", type="string")
        for name in [
            "_normal_", "_normal.",
            "_n_", "_n.",
            "_disp_", "_disp.",
            "_roughness_", "_roughness.",
            "_rmao_", "_rmao.",
        ]:
            if name in image_path_short.lower():
                mc.setAttr(x + ".cs", "Raw", type="string")

                
def check_uv_set_names(self):
    """检查场景中所有模型的 UV 集名称"""
    # 获取所有网格体
    all_meshes = mc.ls(type='mesh', long=True)
    non_standard_uvs = []

    # 检查每个网格体的 UV 集
    for mesh in all_meshes:
        uv_sets = mc.polyUVSet(mesh, query=True, allUVSets=True) or []
        if not uv_sets or uv_sets[0] != 'map1':
            transform = mc.listRelatives(mesh, parent=True, fullPath=True)[0]
            non_standard_uvs.append(transform)

    if non_standard_uvs:
        # 询问用户是否要修改 UV 集名称
        response = mc.confirmDialog(
            title='UV Set 检查',
            message=f'发现 {len(non_standard_uvs)} 个模型的 UV 集名称不是 map1\n是否要重命名为 map1？',
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
                        mc.polyUVSet(mesh, rename=True, uvSet=current_uvs[0], newUVSet='map1')
                        # 如果有多个 UV 集，删除其他的
                        for uv_set in current_uvs[1:]:
                            mc.polyUVSet(mesh, delete=True, uvSet=uv_set)
                    except:
                        print(f"无法重命名 {obj} 的 UV 集")
            mc.confirmDialog(message='UV 集重命名完成', button='确定')
        
        elif response == '选择':
            mc.select(non_standard_uvs)
    else:
        mc.confirmDialog(message='所有模型的 UV 集名称都是 map1', button='确定')

def check_duplicate_names(self):
    """检查场景中是否存在重复命名的物体"""

    # 获取场景中所有的 mesh 节点
    all_meshes = mc.ls(type='mesh', long=True)

    # 创建一个字典来存储名称和对应的物体列表
    name_dict = {}

    # 遍历所有物体，按名称分组
    for mesh in all_meshes:
        # 获取物体的短名称（不包含路径和命名空间）
        short_name = mesh.split('|')[-1].split(':')[-1]

        # 获取 mesh 的 transform 节点
        transform = mc.listRelatives(mesh, parent=True, fullPath=True)[0]

        if short_name not in name_dict:
            name_dict[short_name] = []
        name_dict[short_name].append({
            'mesh': mesh,
            'transform': transform
        })

    # 检查是否有重复命名
    found_duplicates = False

    print("\n=== 重复命名检查结果 ===")
    duplicated_objects = []
    for name, objects in name_dict.items():
        if len(objects) > 1:
            found_duplicates = True

            for obj in objects:
                duplicated_objects.append(obj['transform'])
                print(f"  - Mesh: {obj['mesh']}")
                print(f"    Transform: {obj['transform']}")
                print("    ---")

    if not found_duplicates:
        mc.confirmDialog(m="场景中没有发现重复命名的网格体", b='close')
    else:
        same_name_select = mc.confirmDialog(m="\n发现重复命名的网格体: ", b=[u'选择', u'取消'],
                                            defaultButton='选择', cancelButton='取消')
        if same_name_select == u'选择':
            mc.select([obj for obj in duplicated_objects])

        mc.confirmDialog(m="\n警告：场景中存在重复命名的网格体，这可能会导致导出时出现问题！\n请确保所有网格体名称唯一。",
                         b='close')

def del_all_script():
    """删除所有 含病毒的Script 节点"""
    scripts = mc.ls(type="script")

    if not scripts:
        return

    for script in scripts:
        try:
            # 检查是否包含特定关键字
            if "vaccine_gene" in script or "breed_gene" in script:
                mc.lockNode(script, l=False)
                mc.delete(script)
                continue
            # 解锁并删除节点
            print('Successfully deleted script node: {}'.format(script))
        except Exception as e:
            print('Failed to delete script node "{}": {}'.format(script, e))


def remove_namespace(self):
    default_namespace = ['UI', 'shared']
    mc.namespace(set=':')
    root_namespace = mc.namespaceInfo(listOnlyNamespaces=1)
    for i in root_namespace:
        if i not in default_namespace:
            mc.namespace(removeNamespace=':' + i, mergeNamespaceWithRoot=True)


def addRSAOVnameWinUI(self):
    rsAOVname = mc.ls(type='RedshiftAOV')
    if mc.window('aovPathModify', ex=1):
        mc.deleteUI('aovPathModify', wnd=1)
    mc.window('aovPathModify', t=u'修改RS_AOV中的名称路径', widthHeight=(
        250, 250), s=0, resizeToFitChildren=1, mnb=0, mxb=0)
    mc.columnLayout(adj=1)
    mc.text(label=u'这里用来修改RedShift中，每一层AOV中的File Name Prefix这个属性中的路径')
    mc.separator(height=5, style='in')
    nameOfPrefix = mc.textField('RS_AOV_namePrefix', tx='')
    mc.button(l=u'修改/添加', c=renameRSAOVprefix)
    # mc.textFieldButtonGrp('RS_AOV_namePrefix', l='File Name Prefix名称 ', text='',buttonLabel='运行',buttonCommand=renameRSAOVprefix)
    mc.showWindow()


def build_ui():
    """构建主界面"""
    if mc.window('zxtSCNclearUp', exists=True):
        mc.deleteUI('zxtSCNclearUp')

    window = mc.window('zxtSCNclearUp',
                       title=u'Maya场景清理工具',
                       widthHeight=(400, 700),
                       resizeToFitChildren=True)

    main_layout = mc.columnLayout(adjustableColumn=True, rowSpacing=5, columnOffset=('both', 5))

    # 头部信息
    mc.frameLayout(label=u'关于', collapsable=True, collapse=True)
    mc.columnLayout(adjustableColumn=True, rowSpacing=3)
    mc.text(label=u'Author: 威武的天哥', align='left')
    mc.text(label=u'E-mail: johnny.zxt@gmail.com', align='left')
    mc.text(label=u'Created: ' + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), align='left')
    mc.setParent('..')
    mc.setParent('..')

    # 变换工具部分
    mc.frameLayout(label=u'变换工具', collapsable=True, collapse=False)
    mc.columnLayout(adjustableColumn=True, rowSpacing=3)
    mc.text(label=u'用于复制物体A到指定位置B\n先选择物体A后选择其它物体所在的位置\n就算冻结过也无所谓',
            align='left', fn='fixedWidthFont')
    mc.separator(height=5, style='in')
    mc.rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 190), (2, 190)], columnSpacing=(2, 5))
    mc.button(label=u'复制', command=dup_to_pos, height=30)
    mc.button(label=u'关联复制', command=instance_to_pos, height=30)
    mc.setParent('..')
    mc.setParent('..')
    mc.setParent('..')

    # 材质管理部分
    mc.frameLayout(label=u'材质管理', collapsable=True, collapse=False)
    mc.columnLayout(adjustableColumn=True, rowSpacing=3)
    mc.text(label=u'重命名所有的shader，并把shader名称改为与模型相同\nVR是Vray, RS是RedShift',
            align='left', bgc=(0.6, 0.5, 0.4))
    mc.separator(height=5, style='in')
    mc.textFieldButtonGrp('renameShaderPrefix',
                          label=u'添加shader前缀',
                          text='M_RS_',
                          buttonLabel=u'运行',
                          buttonCommand=renameShader)
    mc.button(label=u'选择检查按面赋予的材质', command=chkShadToFace)
    mc.setParent('..')
    mc.setParent('..')

    # 场景清理部分
    mc.frameLayout(label=u'场景清理', collapsable=True, collapse=False)
    mc.columnLayout(adjustableColumn=True, rowSpacing=3)
    mc.text(label=u'清理场景中的各种问题节点', align='left', bgc=(0.4, 0.4, 0.4))
    mc.separator(height=5, style='in')

    cleanup_buttons = [
        (u'清除垃圾插件信息', clean_plugins),
        (u'清除垃圾节点类型 Unknown', clean_unknown_nodes),
        (u'检查重复命名的物体', check_duplicate_names),
        (u'检查UV集名称', check_uv_set_names),
        (u'清除 vaccine', clean_virus),
        (u'清除 CgAbError', clearCGABError),
        (u'清除 onModelChange3dc ', clean_on_model_change3dc),
        (u'清除 lockNode error ', optimize_scene),
        (u'清除 pasted_ 节点名字', del_pasted_name),
        (u'清除 Intermediate 的 shape 节点', clearIntermediateObj),
        (u'清除 transform 下多余的 shape 节点', del_multi_shapes),
        (u'清除空的组', clearEmptyTransform)
    ]

    for label, cmd in cleanup_buttons:
        mc.button(label=label, command=cmd, height=25)

    mc.setParent('..')
    mc.setParent('..')

    # 渲染器管理部分
    mc.frameLayout(label=u'渲染器管理', collapsable=True, collapse=False)
    mc.columnLayout(adjustableColumn=True, rowSpacing=3)

    # VRay设置
    mc.frameLayout(label=u'VRay设置', collapsable=True, collapse=False)
    mc.columnLayout(adjustableColumn=True, rowSpacing=3)
    mc.button(label=u'初始化VRay渲染设置', command=init_vr_renderer)
    mc.button(label=u'添加AOV', command=add_aov_vr)
    mc.button(label=u'添加细分及细分控制', command=build_subdive_win_ui)
    mc.setParent('..')
    mc.setParent('..')

    # RedShift设置
    mc.frameLayout(label=u'RedShift设置', collapsable=True, collapse=False)
    mc.columnLayout(adjustableColumn=True, rowSpacing=3)
    mc.button(label=u'AOV路径prefix修改', command=addRSAOVnameWinUI)
    mc.setParent('..')
    mc.setParent('..')

    # 其他渲染器清理
    mc.frameLayout(label=u'其他渲染器清理', collapsable=True, collapse=False)
    mc.columnLayout(adjustableColumn=True, rowSpacing=3)
    mc.button(label=u'清除海龟渲染器残留', command=del_turtle_render)
    mc.button(label=u'清除RenderMan', command=del_renderman)
    mc.button(label=u'清除RenderMan垃圾节点', command=clearMSRenderMan)
    mc.button(label=u'清除renderGlobal中的yeti信息', command=clearMSRenderGloble)
    mc.button(label=u'修复渲染层切换Bug', command=renderLayerBugFix)
    mc.setParent('..')
    mc.setParent('..')

    mc.setParent('..')
    mc.setParent('..')

    mc.showWindow(window)


if __name__ == '__main__':
    build_ui()
