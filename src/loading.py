import xml.etree.ElementTree as ET
import easygui
from smart_connections import Connection
from PyQt5.QtCore import QPoint

def create_connections(main_win, connections, color):
    for connection in connections.findall('Connection'):
        source = connection.get('Source')
        destination = connection.get('Destination')
        name_source, source_element = source.split('.')
        name_dest, dest_element = destination.split('.')
        dx1 = connection.get('dx1')
        dx2 = connection.get('dx2')
        dy1 = connection.get('dy')
        if dx1:
            dx1 = int(float(dx1) / main_win.coords_coef)
        if dx2:
            dx2 = int(float(dx2) / main_win.coords_coef)
        if dy1:
            dy1 = int(float(dy1) / main_win.coords_coef)

        for block in main_win.list_blocks:
            if block.name == name_source:
                for rect in block.rectangles[1:]:
                    if rect.name == source_element:
                        main_win.source_element = rect
            if block.name == name_dest:
                for rect in block.rectangles[1:]:
                    if rect.name == dest_element:
                        main_win.destination_element = rect

        main_win.current_connection = Connection(
            QPoint(main_win.source_element.right() + 1, main_win.source_element.center().y()),
            QPoint(main_win.destination_element.left() - 1, main_win.destination_element.center().y()), color=color)
        if main_win.current_connection.simple:
            main_win.current_connection.simple_case(dx1=dx1)
        else:
            main_win.current_connection.hard_case(dx1=dx1, dx2=dx2, dy1=dy1)
        main_win.destination_element.connect_lines.append(main_win.current_connection)
        main_win.source_element.connect_lines.append(main_win.current_connection)
        main_win.source_element.parent.connections[main_win.source_element.name].append(
            (main_win.destination_element.parent.name, main_win.destination_element.name))
        main_win.polylines_list.append(main_win.current_connection)
        main_win.current_connections = None


def read_xml(main_win):
    try:
        main_win.clear()
        input_file = easygui.fileopenbox(filetypes=["*.xml"])
        main_win.file_path = input_file
        tree = ET.parse(input_file)
        root = tree.getroot()
        device = root.find('Device')
        resource = device.find('Resource')
        fb_network = resource.find('FBNetwork')
        main_win.create_block_Start()

        for fb in fb_network.findall('FB'):  # Создаём FB
            name = fb.get('Name')
            block_type = fb.get('Type')
            x = int(float(fb.get('x')) / main_win.coords_coef)
            y = int(float(fb.get('y')) / main_win.coords_coef)
            current_fb = main_win.create_block_dict[block_type](main_win, name=name, x=x, y=y)
            main_win.list_blocks.append(current_fb)
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
        create_connections(main_win, event_connections, 'red')
        create_connections(main_win, data_connections, 'blue')
        main_win.update_all()
    except Exception as e:
        print("File reading error")
        print(e)