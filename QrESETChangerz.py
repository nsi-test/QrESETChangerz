#my thngs
import json
import qrcode #for qr encode

#pyzbar variant for decode
from PIL import Image
from pyzbar.pyzbar import decode

#my constant thngs

EES_DOWNLOAD_LOCATION = 'https://repository.eset.com/v1/com/eset/apps/business/ees/android/v5/5.1.2.0/ees.apk'

EQR_PROGRAM_VERSION = '1.1.1' #x.x.x version

EQR_LAST_FOLDER_REG_BASE = r'SOFTWARE\EQR\QrESETChangerz' #raw string

#/my constant thngs

# The 'pythonnet' library allows interaction with the .NET Common Language Runtime (CLR).
# We'll use it here to access the System.Windows.Forms library for GUI elements.
import clr
import sys
import os
import threading # Import the threading module

# --- Prerequisites Check ---
# This script is designed for Windows, as it uses the Windows Forms library.
# The .NET Framework must be installed on the system.
if sys.platform != 'win32':
    print("Warning: This script is primarily intended for a Windows environment.")
    print("It uses System.Windows.Forms which is part of the .NET Framework.")
    # You might need to configure Mono on other platforms to run this.
    # For now, we will proceed assuming a compatible environment.

# --- Add .NET Assembly References ---
# This step loads the necessary .NET libraries into the Python process.
# System.Windows.Forms contains the GUI components (Form, Button, Dialog).
# System.Drawing is needed for objects like Size and Point.
try:
    clr.AddReference("System.Windows.Forms")
    clr.AddReference("System.Drawing")
except IOError as e:
    print(f"Error: Could not add .NET assembly references. Check your pythonnet installation and .NET Framework.")
    print(f"Details: {e}")
    sys.exit(1)

# --- Import .NET Classes ---
# Now that the assemblies are referenced, we can import specific classes.
# We've added MessageBoxButtons here to fix the AttributeError.
from System.Windows.Forms import (
    Application,
    Form,
    Button,
    OpenFileDialog,
    SaveFileDialog,
    DialogResult,
    MessageBox,
    MessageBoxButtons # Added this import
)
from System.Drawing import Size, Point, Font

from winreg import * #for registry access

from pathlib import Path #for path manipulations

# --- Main Application Class ---
# This class defines our GUI form. It inherits from the .NET Form class.
class FilePickerApp(Form):
    def __init__(self):
        # Call the base class constructor first. This is a good practice to ensure
        # the underlying .NET object is fully initialized.
        super().__init__()
        
        # Set up the basic properties of the form
        self.Text = "ESET QR changer to esa 5" + " v" + EQR_PROGRAM_VERSION
        self.Size = Size(450, 250)
        self.CenterToScreen()  # Center the form on the screen

        # This variable will store the content of the selected file
        self.file_content = None

        # Create a button
        self.pick_file_button = Button()
        self.pick_file_button.Text = "Select a QR provisioning picture"
        self.pick_file_button.Size = Size(150, 65)
        
        # Position the button in the center of the form
        button_x = (self.ClientSize.Width - self.pick_file_button.Width) // 2
        button_y = (self.ClientSize.Height - self.pick_file_button.Height) // 2
        self.pick_file_button.Location = Point(button_x, button_y)
        
        # Set a slightly larger font for better readability
        self.pick_file_button.Font = Font("Arial", 12)

        # Add the button to the form's controls
        self.Controls.Add(self.pick_file_button)

        # Register an event handler for the button's Click event.
        # This tells the button to call our 'on_button_click' method when pressed.
        #self.pick_file_button.Click += self.on_button_click
        self.pick_file_button.Click += self.on_button_click

        #my thngs
        self.file_path = "" #initially empty
        self.open_folder_path  = "" #initially empty
        #/my thngs

    def on_button_click(self, sender, args):
        """
        This method is called when the 'Select a File' button is clicked.
        It now starts a new thread to open the file dialog to prevent the UI from freezing.
        """
        # Create a new thread to run the file dialog logic
        thread = threading.Thread(target=self._show_file_dialog)
        thread.daemon = True # Allows the application to exit even if the thread is running
        thread.start()

    def _show_file_dialog(self):
        """
        This method contains the file dialog logic and file reading.
        It runs on a separate thread.
        """
        # Create an instance of the OpenFileDialog class
        open_dialog = OpenFileDialog()
        open_dialog.Title = "Please choose a file"
        
        # Set a filter to show only specific file types (optional but good practice)
        open_dialog.Filter = "Png files (*.png)|*.png|All files (*.*)|*.*" #my thngs

        cwdpath = os.getcwd() #where the program is
        last_folder = self._get_last_folder_reg(cwdpath)

        open_dialog.InitialDirectory = last_folder
        print(f"initial directory is {open_dialog.InitialDirectory}")


        # Show the dialog and check the result
        dialog_result = open_dialog.ShowDialog()

        if dialog_result == DialogResult.OK:
            # The user selected a file. Get the full path.
            file_path = open_dialog.FileName
            
            #my th
          
            folder_path = Path(file_path).parent
            print(f"open folder path is: {folder_path}")
            self.open_folder_path = str(folder_path)
            self._set_last_folder_reg(self.open_folder_path)
            
            self.file_path = file_path
            
            #mythngs
            img = self._replace_path_in_png()

            save_dialog = SaveFileDialog()

            save_dialog.Title = "Please choose a file name for the new QR image to save"

            save_dialog.Filter = "PNG (*.png)|*.png|All files (*.*)|*.*"

            cwdpath = os.getcwd() 
            
            save_dialog.InitialDirectory = str(self.open_folder_path)
            print(f"initial directory is {save_dialog.InitialDirectory}")

            save_dialog_result = save_dialog.ShowDialog()

            if save_dialog_result == DialogResult.OK:
                save_file_path = save_dialog.FileName
                print(f"the file to be written is: {save_file_path}")

                try:
                    img.save(save_file_path)
                except Exception as e:
                    MessageBox.Show(self, f"An error occurred while saving the file: {e}",
                                "Error", MessageBoxButtons.OK)
                    
                
                if os.path.isfile(save_file_path):
                    MessageBox.Show(self, f"The file {save_file_path} was successfully written",
                                "Info", MessageBoxButtons.OK)
                else:
                    MessageBox.Show(self, f"The file {save_file_path} was not written, some error occured",
                                "Error", MessageBoxButtons.OK)
            #/mythngs

        elif dialog_result == DialogResult.Cancel:
            # The user cancelled the dialog
            # Corrected: We now use MessageBoxButtons.OK
            MessageBox.Show(self, "File selection was cancelled.", "Cancelled", MessageBoxButtons.OK)
            self.file_content = None

    #my qr thngs
    def _replace_path_in_png(self):

        print(f"_replace_path_in_png begins with path: {self.file_path}")

        if not self.file_path:
            print ("no file path, exiting")
            return

        #decoding part         
        print(f"self.file_path before trying to decode: {self.file_path}")

        #pyzbar variant
        try:
            qr_result = decode(Image.open(self.file_path))
        except Exception as ex:
            print("\nAn error occurred getting the image:")
            print(ex)
      
        qr_text = qr_result[0].data.decode('utf-8')  

        print(f"qr_text should be: {qr_text}")

        if not qr_text:
            MessageBox.Show(self, f"the QR image is not appropriate",
            "Error", MessageBoxButtons.OK)
            self.file_path = None # clear the bad path

        #json part
        jqr = json.loads(qr_text)

        print(f"current file download location is : {jqr['android.app.extra.PROVISIONING_DEVICE_ADMIN_PACKAGE_DOWNLOAD_LOCATION']}")

        jqr['android.app.extra.PROVISIONING_DEVICE_ADMIN_PACKAGE_DOWNLOAD_LOCATION'] = EES_DOWNLOAD_LOCATION
        
        qr_text2 = json.dumps(jqr)

        #encoding part
        qr = qrcode.QRCode(version=5,error_correction=qrcode.constants.ERROR_CORRECT_L,box_size=10,border=4,)
        
        qr.add_data(qr_text2)

        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        return img

        #/my qr thngs

    #/f-n _replace_path_in_png

    #registry access thngs
    def _get_last_folder_reg(self, value_when_empty):
        try:
            base_key = OpenKey(HKEY_CURRENT_USER, EQR_LAST_FOLDER_REG_BASE, 0, KEY_ALL_ACCESS)
            last_folder = QueryValueEx(base_key, "LastFolder")[0]
            CloseKey(base_key)
            return last_folder
        except:
            base_key = CreateKeyEx(HKEY_CURRENT_USER, EQR_LAST_FOLDER_REG_BASE)
            SetValueEx(base_key, "LastFolder", 0, REG_SZ, value_when_empty)
            CloseKey(base_key)
            return value_when_empty
    #/f-n _get_last_folder_reg

    def _set_last_folder_reg(self, folder_path):
        try:
            base_key = OpenKey(HKEY_CURRENT_USER, EQR_LAST_FOLDER_REG_BASE, 0, KEY_ALL_ACCESS)
            SetValueEx(base_key, "LastFolder", 0, REG_SZ, folder_path)
            CloseKey(base_key)
        except Exception as e:
            print(f"Error setting registry value: {e}")

#/class FilePickerApp

# --- Entry Point ---
# The standard way to run the application
if __name__ == "__main__":
    try:
        # Create an instance of our form
        app_form = FilePickerApp()
        
        # Run the application. This starts the GUI event loop.
        Application.Run(app_form)
        
        # After the form is closed, you can still access the file_content variable.
        # Note: The app will block at Application.Run() until the form is closed.
        if app_form.file_content:
            print("\nApplication closed.")
            print(f"The content of the last selected file is still available. Length: {len(app_form.file_content)}")
        else:
            print("\nApplication closed. No file was selected or an error occurred.")
    except Exception as ex:
        print("\nAn unexpected error occurred during application runtime:")
        print(ex)
        print("\nPlease ensure that the .NET Framework is correctly installed and accessible by pythonnet.")
