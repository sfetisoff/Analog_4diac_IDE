import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime


def create_xml(list_blocks, block_start):
    coords_coef = 4
    # Создаем корневой элемент
    name_project = 'Original_project'
    date = datetime.now().strftime("%Y-%m-%d")

    root = ET.Element("System", Name=name_project, Comment="")
    version_info = ET.SubElement(root, "VersionInfo", Version="1.0", Author="Simon", Date=date)
    application = ET.SubElement(root, "Application", Name=f"{name_project}App", Comment="")
    sub_app_network = ET.SubElement(application, "SubAppNetwork")

    for block in list_blocks:
        if block is not block_start:
            fb = ET.SubElement(sub_app_network, "FB", Name=block.name, Type=block.type, Comment="", x=str(block.x * coords_coef), y=str(block.y * coords_coef))

    event_connections = ET.SubElement(sub_app_network, "EventConnections")
    data_connections = ET.SubElement(sub_app_network, "DataConnections")
    data_elements = ["IN","OUT","QO","QI",'LABEL']

    for block in list_blocks:
        if block is not block_start:
            for source_el, ar_elements in block.connections.items():
                if ar_elements:
                    for dest_block_name, dest_el in ar_elements:
                        if (dest_el in data_elements) or (source_el in data_elements):
                            connection = ET.SubElement(data_connections, "Connection",
                                                       Source=f"{block.name}.{source_el}",
                                                       Destination=f"{dest_block_name}.{dest_el}", Comment="")
                        else:
                            connection = ET.SubElement(event_connections, "Connection",
                                                       Source=f"{block.name}.{source_el}",
                                                       Destination=f"{dest_block_name}.{dest_el}", Comment="")

    device = ET.SubElement(root, "Device", Name="FORTE_PC", Type="FORTE_PC", Comment="", x="693.3333333333334", y="653.3333333333334")
    parameter_device = ET.SubElement(device, "Parameter", Name="MGR_ID", Value='"localhost:61499"')
    attribute1 = ET.SubElement(device, "Attribute", Name="Profile", Type="STRING", Value="HOLOBLOC", Comment="device profile")
    attribute2 = ET.SubElement(device, "Attribute", Name="Color", Type="STRING", Value="255,190,111", Comment="color")
    resource = ET.SubElement(device, "Resource", Name="EMB_RES", Type="EMB_RES", Comment="", x="0.0", y="0.0")
    fb_network = ET.SubElement(resource, "FBNetwork")
    for block in list_blocks:
        if block is not block_start:
            fb = ET.SubElement(fb_network, "FB", Name=block.name, Type=block.type, Comment="", x=str(block.x * coords_coef), y=str(block.y * coords_coef))

    event_connections_fb = ET.SubElement(fb_network, "EventConnections")
    data_connections_fb = ET.SubElement(fb_network, "DataConnections")

    for block in list_blocks:
        for source_el, ar_elements in block.connections.items():
            if ar_elements:
                for dest_block_name, dest_el in ar_elements:
                    if (dest_el in data_elements) or (source_el in data_elements):
                        connection = ET.SubElement(data_connections_fb, "Connection",
                                                   Source=f"{block.name}.{source_el}",
                                                   Destination=f"{dest_block_name}.{dest_el}", Comment="")
                    else:
                        connection = ET.SubElement(event_connections_fb, "Connection",
                                                   Source=f"{block.name}.{source_el}",
                                                   Destination=f"{dest_block_name}.{dest_el}", Comment="")

    segment = ET.SubElement(root, "Segment", Name="Ethernet", Type="Ethernet", Comment="", x="1733.3333333333335", y="1600.0", dx1="2000.0")
    attribute_segment = ET.SubElement(segment, "Attribute", Name="Color", Type="STRING", Value="161,130,236", Comment="color")
    link = ET.SubElement(root, "Link", SegmentName="Ethernet", CommResource="FORTE_PC", Comment="")

    # Создаем дерево элементов
    tree = ET.ElementTree(root)
    xml_str = ET.tostring(root, encoding='utf-8', method='xml')
    # Используем minidom для форматирования
    parsed_xml = minidom.parseString(xml_str)
    pretty_xml = parsed_xml.toprettyxml(indent="    ")

    # Записываем отформатированный XML в файл
    with open("output_xml.xml", "w", encoding='utf-8') as fh:
        fh.write(pretty_xml)

    print("Отформатированный XML-файл успешно создан.")
