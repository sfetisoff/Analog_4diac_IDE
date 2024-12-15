import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime
import easygui


def create_fboot(list_blocks, block_start, with_gui=True):
    content = []
    content.append(f';<Request ID="2" Action="CREATE"><FB Name="EMB_RES" Type="EMB_RES" /></Request>')
    request_id = 3

    for block in list_blocks:
        if block is not block_start:
            content.append(
                f'EMB_RES;<Request ID="{request_id}" Action="CREATE"><FB Name="{block.name}" Type="{block.type}" /></Request>')
            request_id += 1
        for rect in block.rectangles:
            if rect.value.isdigit():
                content.append(
                    f'EMB_RES;<Request ID="{request_id}" Action="WRITE"><Connection Source="{rect.value}" Destination="{block.name}.{rect.name}" /></Request>')
                request_id += 1
            if (rect.value.isdigit() is False) and (rect.value != "''"):
                content.append(
                    f'EMB_RES;<Request ID="{request_id}" Action="WRITE"><Connection Source="&apos;{rect.value[1:-1]}&apos;" Destination="{block.name}.{rect.name}" /></Request>')
                request_id += 1

    for block in list_blocks:
        for source_el, ar_elements in block.connections.items():
            if ar_elements:
                for dest_block_name, dest_el in ar_elements:
                    content.append(
                        f'EMB_RES;<Request ID="{request_id}" Action="CREATE"><Connection Source="{block.name}.{source_el}" Destination="{dest_block_name}.{dest_el}" /></Request>')
                    request_id += 1

    content.append(f'EMB_RES;<Request ID="{request_id - 1}" Action="START"/>')
    if with_gui:
        file_path = easygui.filesavebox(
            title="Create fboot",
            default="*.fboot",
            filetypes=["*.fboot"]
        )
    else:
        file_path = '../project_files/deploy.fboot'
    try:
        # Записываем отформатированный XML в файл
        with open(file_path, "w", encoding='utf-8') as f:
            for line in content:
                f.write(f'{line}\n')

        print("The fboot file has been successfully created")
    except:
        print("Fboot file creating error")


def create_xml(list_blocks, block_start, coords_coef, with_gui=True, old_file_path='../project_files/project1.xml'):
    def find_connection(source_block, dest_block_name, source_el_name, dest_el_name):
        for block in list_blocks:
            if block.name == dest_block_name:
                dest_block = block
                break
        for rect in source_block.rectangles:
            if rect.name == source_el_name:
                source_el = rect
                break
        for rect in dest_block.rectangles:
            if rect.name == dest_el_name:
                dest_el = rect
                break
        for connection1 in source_el.connect_lines:
            for connection2 in dest_el.connect_lines:
                if connection1 == connection2:
                    return connection1

    def write_connections(parent_tag_event, parent_tag_data):
        for source_el, ar_elements in block.connections.items():
            if ar_elements:  # Если у этого элемента есть связи
                for dest_block_name, dest_el in ar_elements:
                    polyline = find_connection(block, dest_block_name, source_el, dest_el)
                    if (dest_el in data_elements) or (source_el in data_elements):
                        connection = ET.SubElement(parent_tag_data, "Connection",
                                                   Source=f"{block.name}.{source_el}",
                                                   Destination=f"{dest_block_name}.{dest_el}",
                                                   Comment="")
                    else:
                        connection = ET.SubElement(parent_tag_event, "Connection",
                                                   Source=f"{block.name}.{source_el}",
                                                   Destination=f"{dest_block_name}.{dest_el}",
                                                   Comment="")
                    if polyline.dx1:
                        connection.set('dx1', str(polyline.dx1 * coords_coef))
                    if polyline.dx2:
                        connection.set('dx2', str(polyline.dx2 * coords_coef))
                    if polyline.dy1:
                        connection.set('dy', str(polyline.dy1 * coords_coef))

    # Создаем корневой элемент
    name_project = 'Original_project'
    date = datetime.now().strftime("%Y-%m-%d")

    root = ET.Element("System", Name=name_project, Comment="")
    version_info = ET.SubElement(root, "VersionInfo", Version="1.0", Author="Simon", Date=date)
    application = ET.SubElement(root, "Application", Name=f"{name_project}App", Comment="")
    sub_app_network = ET.SubElement(application, "SubAppNetwork")

    for block in list_blocks:
        if block is not block_start:
            fb = ET.SubElement(sub_app_network, "FB", Name=block.name, Type=block.type, Comment="",
                               x=str(block.x * coords_coef), y=str(block.y * coords_coef))
            for rect in block.rectangles:
                if rect.value != "''":
                    parameter = ET.SubElement(fb, "Parameter", Name=rect.name, Value=str(rect.value))

    event_connections = ET.SubElement(sub_app_network, "EventConnections")
    data_connections = ET.SubElement(sub_app_network, "DataConnections")
    data_elements = ["IN", "OUT", "QO", "QI", 'LABEL']

    for block in list_blocks:
        if block is not block_start:
            write_connections(event_connections, data_connections)

    device = ET.SubElement(root, "Device", Name="FORTE_PC", Type="FORTE_PC", Comment="", x="693.3333333333334",
                           y="653.3333333333334")
    parameter_device = ET.SubElement(device, "Parameter", Name="MGR_ID", Value='"localhost:61499"')
    attribute1 = ET.SubElement(device, "Attribute", Name="Profile", Type="STRING", Value="HOLOBLOC",
                               Comment="device profile")
    attribute2 = ET.SubElement(device, "Attribute", Name="Color", Type="STRING", Value="255,190,111", Comment="color")
    resource = ET.SubElement(device, "Resource", Name="EMB_RES", Type="EMB_RES", Comment="", x="0.0", y="0.0")
    fb_network = ET.SubElement(resource, "FBNetwork")
    for block in list_blocks:
        if block is not block_start:
            fb = ET.SubElement(fb_network, "FB", Name=block.name, Type=block.type, Comment="",
                               x=str(block.x * coords_coef), y=str(block.y * coords_coef))
            for rect in block.rectangles:
                if rect.value != "''":
                    parameter = ET.SubElement(fb, "Parameter", Name=rect.name, Value=str(rect.value))

    event_connections_fb = ET.SubElement(fb_network, "EventConnections")
    data_connections_fb = ET.SubElement(fb_network, "DataConnections")

    for block in list_blocks:
        write_connections(event_connections_fb, data_connections_fb)

    segment = ET.SubElement(root, "Segment", Name="Ethernet", Type="Ethernet", Comment="", x="1733.3333333333335",
                            y="1600.0", dx1="2000.0")
    attribute_segment = ET.SubElement(segment, "Attribute", Name="Color", Type="STRING", Value="161,130,236",
                                      Comment="color")
    link = ET.SubElement(root, "Link", SegmentName="Ethernet", CommResource="FORTE_PC", Comment="")

    # Создаем дерево элементов
    tree = ET.ElementTree(root)
    xml_str = ET.tostring(root, encoding='utf-8', method='xml')
    # Используем minidom для форматирования
    parsed_xml = minidom.parseString(xml_str)
    pretty_xml = parsed_xml.toprettyxml(indent="    ")

    if with_gui:
        file_path = easygui.filesavebox(
            title="Save file",
            default="*.xml",
            filetypes=["*.xml"]
        )
    else:
        file_path = old_file_path
    try:
        # Записываем отформатированный XML в файл
        with open(file_path, "w", encoding='utf-8') as fh:
            fh.write(pretty_xml)

        print("The XML file has been successfully created")
    except:
        print("XML file saving error")
