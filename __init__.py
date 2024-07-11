# -*- coding: utf-8 -*-
# Copyright (c) 2024 Dominic Hock

""""
Control bluetooth devices using albert
"""

import os
from sqlite3 import connect
import subprocess
from typing import List

from albert import *

md_iid = "2.3"
md_version = "1.0"
md_name = "Bluetooth"
md_description = "Control bluetooth devices"
md_license = "GPL-3.0"
md_url = "https://github.com/subtixx/albert-btctl"
md_maintainers = "@subtixx"
md_bin_dependencies = ["bluetoothctl"]

class BluetoothDevice:
    id: str
    name: str
    connected: bool
    icon: str|None # ex audio-headphones
    
    def __init__(self, id, name, icon=None, connected=False):
        self.id = id
        self.name = name
        self.icon = icon
        self.connected = connected

    def __str__(self):
        return self.name
    
    def disconnect(self, workingDir):
        if not self.connected:
            return
        runDetachedProcess(cmdln=['bluetoothctl', 'disconnect', self.id], workdir=workingDir)
        self.connected = False

    def connect(self, workingDir):
        if self.connected:
            return
        runDetachedProcess(cmdln=['bluetoothctl', 'connect', self.id], workdir=workingDir)
        self.connected = True
        
    def rankItem(self) -> RankItem:
        return RankItem(self.item(), 0.0 if self.connected else 1.0)
    
    def getIcon(self) -> str:
        if self.icon is None or self.connected is False:
            return 'xdg:bluetooth-active' if self.connected else 'xdg:bluetooth-disabled'
        
        return 'xdg:' + self.icon
        
    def item(self) -> StandardItem:
        return StandardItem(
            id=self.id,
            text=(f'Connect' if not self.connected else f'Disconnect') + ' ' + self.name,
            subtext=self.id,
            iconUrls=[
                self.getIcon(),
                os.path.dirname(__file__) + (f'/bluetooth-active.svg' if self.connected else '/bluetooth-disabled.svg')
            ],
            actions=[
                Action(
                    id='connect',
                    text='Connect',
                    callable=lambda: self.connect(os.path.dirname(__file__))
                ) if not self.connected else
                Action(
                    id='disconnect',
                    text='Disconnect',
                    callable=lambda: self.disconnect(os.path.dirname(__file__))
                )
            ]
        )

class BluetoothControl:
    currentWorkingDir : str
    
    def __init__(self):
        """
        Initializes the class instance with the current working directory.

        This method sets the `currentWorkingDir` attribute of the class instance
        to the directory containing the current file. It uses the `os.path.dirname()`
        function to get the directory name of the current file.

        Parameters:
            None

        Returns:
            None
        """
        self.currentWorkingDir = os.path.dirname(__file__)
        
    def deviceInfo(self, id) -> BluetoothDevice:
        """
        Retrieves information about a Bluetooth device specified by its ID using 'bluetoothctl info' command.
        
        Parameters:
            id (str): The ID of the Bluetooth device.
            
        Returns:
            BluetoothDevice: A BluetoothDevice object representing the device with the provided ID.
        """
        proc = subprocess.run(['bluetoothctl', 'info', id], stdout=subprocess.PIPE)
        name = 'Bluetooth Device ' + id
        connected = False
        icon = None
        for x in proc.stdout.decode().splitlines():
            currentLine = x.strip()
            key, rawValue = currentLine.split(':', 1)
            key = key.strip().lower()
            value = rawValue.strip().lower()
            if key == 'name':
                name = rawValue.strip()
            elif key == 'connected':
                connected = value == 'yes'
            elif key == 'icon':
                icon = value
        return BluetoothDevice(id, name, icon, connected)
        
    def listDevices(self) -> List[BluetoothDevice]:
        """
        Retrieves a list of Bluetooth devices by running 'bluetoothctl devices' command.
        Parses the output to extract device ID and name, creates a new BluetoothDevice object for each device, and appends it to the deviceList.
        
        Returns a list of BluetoothDevice objects representing the available devices.
        """
        deviceList : List[BluetoothDevice] = []
        
        proc = subprocess.run(['bluetoothctl', 'devices'], stdout=subprocess.PIPE)
        for x in proc.stdout.decode().splitlines():
            id, _ = x.removeprefix('Device ').split(' ', 1)
            deviceList.append(self.deviceInfo(id))
            
        return deviceList
    
    def listConnectedDevices(self) -> List[BluetoothDevice]:
        """
        Retrieves a list of connected Bluetooth devices by running 'bluetoothctl devices Connected' command.
        Parses the output to extract device ID and name, creates a new BluetoothDevice object for each device, and appends it to the deviceList.
        
        Returns a list of BluetoothDevice objects representing the connected devices.
        """
        deviceList : List[BluetoothDevice] = []
        
        proc = subprocess.run(['bluetoothctl', 'devices', 'Connected'], stdout=subprocess.PIPE)
        for x in proc.stdout.decode().splitlines():
            id, _ = x.removeprefix('Device ').split(' ', 1)
            deviceList.append(self.deviceInfo(id))
            
        return deviceList
        
    def disconnectDevice(self, btDevice: str|BluetoothDevice):
        """
        Disconnects a Bluetooth device.

        Args:
            btDevice (str | BluetoothDevice): The Bluetooth device to disconnect. It can be either a string representing the device ID or a BluetoothDevice object.

        Returns:
            None

        This function disconnects a Bluetooth device by running the 'bluetoothctl disconnect' command. It first checks if the `btDevice` argument is an instance of the `BluetoothDevice` class. If it is, it retrieves the device ID from the `id` attribute of the `btDevice` object. Otherwise, it assumes that the `btDevice` argument is a string representing the device ID. It then runs the 'bluetoothctl disconnect' command with the device ID as an argument. The working directory for the command is set to the `currentWorkingDir` attribute of the current instance.
        """
        if isinstance(btDevice, BluetoothDevice):
            btDevice.disconnect(self.currentWorkingDir)
        elif isinstance(btDevice, str):
            runDetachedProcess(cmdln=['bluetoothctl', 'disconnect', btDevice], workdir=self.currentWorkingDir)
        else:
            raise TypeError('btDevice must be either a string or a BluetoothDevice object')
        
    def connectDevice(self, btDevice: str|BluetoothDevice):
        """
        Connects a Bluetooth device.

        Args:
            btDevice (str | BluetoothDevice): The Bluetooth device to connect. It can be either a string representing the device ID or a BluetoothDevice object.

        Returns:
            None

        Raises:
            TypeError: If the `btDevice` argument is neither a string nor a BluetoothDevice object.

        This function connects a Bluetooth device by running the 'bluetoothctl connect' command. It first checks if the `btDevice` argument is an instance of the `BluetoothDevice` class. If it is, it retrieves the device ID from the `id` attribute of the `btDevice` object. Otherwise, it assumes that the `btDevice` argument is a string representing the device ID. It then runs the 'bluetoothctl connect' command with the device ID as an argument. The working directory for the command is set to the `currentWorkingDir` attribute of the current instance.

        Note:
            The `runDetachedProcess` function is used to run the 'bluetoothctl connect' command in a detached process.
        """
        if isinstance(btDevice, BluetoothDevice):
            btDevice.connect(self.currentWorkingDir)
        elif isinstance(btDevice, str):
            runDetachedProcess(cmdln=['bluetoothctl', 'connect', btDevice], workdir=self.currentWorkingDir)
        else:
            raise TypeError('btDevice must be either a string or a BluetoothDevice object')

class Plugin(PluginInstance, IndexQueryHandler):
    bluetoothControl : BluetoothControl = BluetoothControl()
    bluetoothDevices : List[BluetoothDevice] = []

    def __init__(self):
        PluginInstance.__init__(self)
        IndexQueryHandler.__init__(
            self,
            id='bt',
            name=md_name,
            description=md_description
        )
        
    def updateIndexItems(self):
        self.bluetoothDevices = []
        
        devices = self.bluetoothControl.listDevices()
        for device in devices:
            self.bluetoothDevices.append(device)
        
    def handleGlobalQuery(self, query: Query) -> List[RankItem]:
        if query.trigger == '':
            return []
        
        filtered : List[RankItem] = []
        
        s = query.string.strip().lower()
        for device in self.bluetoothDevices:
            if not s or s in device.name.lower():
                filtered.append(device.rankItem())
            
        return filtered
