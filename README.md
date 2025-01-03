# Orion Star A200 driver
This driver is to collect data from the pH and conductivity probe located in BonLab. The Orion Star meter (*the fancy one*) can be connected to a lab labtop using a mini usb cable, once connected, check device manager for the com port that was assigned and check this is the same as within the script; it should look something like 'COM7'. After this, the script can be run, this will log data at the interval indicated within the script to the same directory as the probe, with a default file name, both of which can be edited. 

For integration to the pumps see the Harvard driver page for the script. 
