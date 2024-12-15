import xml.etree.ElementTree as ET
import easygui
from smart_connections import Connection
from PyQt5.QtCore import QPoint
import custom_blocks as cb

def create_connections(main_window, connections, color):
    for connection in connections.findall('Connection'):
        source = connection.get('Source')
        destination = connection.get('Destination')
        name_source, source_element = source.split('.')
        name_dest, dest_element = destination.split('.')
        dx1 = connection.get('dx1')
        dx2 = connection.get('dx2')
        dy1 = connection.get('dy')
        if dx1:
            dx1 = int(float(dx1) / main_window.coords_coef)
        if dx2:
            dx2 = int(float(dx2) / main_window.coords_coef)
        if dy1:
            dy1 = int(float(dy1) / main_window.coords_coef)

        for block in main_window.list_blocks:
            if block.name == name_source:
                for rect in block.rectangles[1:]:
                    if rect.name == source_element:
                        main_window.source_element = rect
            if block.name == name_dest:
                for rect in block.rectangles[1:]:
                    if rect.name == dest_element:
                        main_window.destination_element = rect

        main_window.current_connection = Connection(
            QPoint(main_window.source_element.right() + 1, main_window.source_element.center().y()),
            QPoint(main_window.destination_element.left() - 1, main_window.destination_element.center().y()), color=color)
        if main_window.current_connection.simple:
            main_window.current_connection.simple_case(dx1=dx1)
        else:
            main_window.current_connection.hard_case(dx1=dx1, dx2=dx2, dy1=dy1)
        main_window.destination_element.connect_lines.append(main_window.current_connection)
        main_window.source_element.connect_lines.append(main_window.current_connection)
        main_window.source_element.parent.connections[main_window.source_element.name].append(
            (main_window.destination_element.parent.name, main_window.destination_element.name))
        main_window.polylines_list.append(main_window.current_connection)
        main_window.current_connections = None


def read_xml(main_window):
    try:
        main_window.clear()
        input_file = easygui.fileopenbox(filetypes=["*.xml"])
        main_window.file_path = input_file
        tree = ET.parse(input_file)
        root = tree.getroot()
        device = root.find('Device')
        resource = device.find('Resource')
        fb_network = resource.find('FBNetwork')
        cb.create_block_Start(main_window)

        for fb in fb_network.findall('FB'):  # Создаём FB
            name = fb.get('Name')
            block_type = fb.get('Type')
            x = int(float(fb.get('x')) / main_window.coords_coef)
            y = int(float(fb.get('y')) / main_window.coords_coef)
            current_fb = main_window.create_block_dict[block_type](main_window, name=name, x=x, y=y)
            main_window.list_blocks.append(current_fb)
            for parameter in fb.findall('Parameter'):
                name = parameter.get('Name')
                value = parameter.get('Value')
                for rect in current_fb.rectangles:
                    if rect.editable_label:
                        if rect.name == name:
                            rect.value = value
                            rect.editable_label.label.setText(rect.value)

        event_connections = fb_network.find('EventConnections')
        data_connections = fb_network.find('DataConnections')
        create_connections(main_window, event_connections, 'red')
        create_connections(main_window, data_connections, 'blue')
        main_window.update_all()
    except Exception as e:
        print("File reading error")
        print(e)