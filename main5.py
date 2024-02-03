

import sys
from PyQt5.uic import loadUi
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog, QFileDialog, QApplication, QWidget, QVBoxLayout, QMessageBox
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import pandas as pd

from score import calculate_match_score, find_best_placement
from girl import Girl
from placementcenter import PlacementCenter

import sqlite3
import csv  

# Read Placement Centers data from CSV file
def read_placement_centers_from_csv(file_path):
    placement_centers = []

    with open(file_path, mode="r", newline="") as csv_file:
        reader = csv.reader(csv_file)
        header = next(reader)  # Skip the header row

        for row in reader:
            name, district, services_offered, rating, capacity, min_age, max_age = row
            services_offered = services_offered.split(", ")
            rating, capacity, min_age, max_age = float(rating), int(capacity), int(min_age), int(max_age)

            center = PlacementCenter(name, district, services_offered, rating, capacity, min_age, max_age)
            placement_centers.append(center)

    return placement_centers

# Modify the file path according to your actual file location
csv_file_path = "https://raw.githubusercontent.com/sharonjepkosgei/Empower_her/main/placement_centers_data.csv"
centers = pd.read_csv(csv_file_path)

class MatplotlibWidget(QWidget):
    def __init__(self, parent=None):
        super(MatplotlibWidget, self).__init__(parent)

        self.canvas = FigureCanvas(Figure())
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout) 
        
        
class WelcomeScreen(QDialog):
    def __init__(self):
        super(WelcomeScreen, self).__init__()
        loadUi("welcomescreen.ui", self)
        self.login.clicked.connect(self.gotologin)
        self.create.clicked.connect(self.gotocreate)

    def gotologin(self):
        login = LoginScreen()
        login.success_signal.connect(self.show_main_window)
        widget.addWidget(login)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def gotocreate(self):
        create = CreateAccScreen()
        create.success_signal.connect(self.show_main_window)
        widget.addWidget(create)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def show_main_window(self):
        main_window = MainWindow()
        widget.addWidget(main_window)
        widget.setCurrentIndex(widget.currentIndex() + 1)

class LoginScreen(QDialog):
    success_signal = pyqtSignal()

    def __init__(self):
        super(LoginScreen, self).__init__()
        loadUi("login.ui", self)
        self.passwordfield.setEchoMode(QtWidgets.QLineEdit.Password)
        self.login.clicked.connect(self.loginfunction)

    def loginfunction(self):
        user = self.userfield.text()
        password = self.passwordfield.text()

        if len(user) == 0 or len(password) == 0:
            self.error.setText("Please input all fields.")
        else:
            conn = sqlite3.connect("users.db")
            cur = conn.cursor()
            query = 'SELECT password FROM login_info WHERE username =\'' + user + "\'"
            cur.execute(query)
            result_pass = cur.fetchone()

            if result_pass and result_pass[0] == password:
                print("Successfully logged in.")
                self.error.setText("")
                self.success_signal.emit()  # Emit signal to trigger MainWindow
            else:
                self.error.setText("Invalid username or password")

class CreateAccScreen(QDialog):
    success_signal = pyqtSignal()

    def __init__(self):
        super(CreateAccScreen, self).__init__()
        loadUi("createacc.ui", self)
        self.passwordfield.setEchoMode(QtWidgets.QLineEdit.Password)
        self.confirmpasswordfield.setEchoMode(QtWidgets.QLineEdit.Password)
        self.signup.clicked.connect(self.signupfunction)

    def signupfunction(self):
        user = self.emailfield.text()
        password = self.passwordfield.text()
        confirmpassword = self.confirmpasswordfield.text()

        if len(user) == 0 or len(password) == 0 or len(confirmpassword) == 0:
            self.error.setText("Please fill in all inputs.")
        elif password != confirmpassword:
            self.error.setText("Passwords do not match.")
        else:
            conn = sqlite3.connect("users.db")
            cur = conn.cursor()

            user_info = [user, password]
            cur.execute('INSERT INTO login_info (username, password) VALUES (?,?)', user_info)

            conn.commit()
            conn.close()

            QMessageBox.information(self, "Success", "Account created successfully!")
            self.success_signal.emit()  # Emit signal to trigger MainWindow

class MainWindow(QDialog):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi("calculate.ui", self)
        self.calculate.clicked.connect(self.calculate_and_display)
        self.save_button.clicked.connect(self.save_result)
        self.display_button.clicked.connect(self.display_center_statistics)
        self.error.setText("")
        
        # Establish a connection to the SQLite database
        self.conn = sqlite3.connect("survivor.db")
        self.cur = self.conn.cursor()
        
        # Initialize instance variables
        self.girl_name = ""
        self.best_center = None
        self.match_score = 0.0
        
        # Create a QVBoxLayout for your main window
        layout = QVBoxLayout(self)
        self.setLayout(layout)
    

    def calculate_and_display(self):
        # Retrieve user inputs from UI elements
        girl_fname = self.f_name.text()
        girl_lname = self.l_name.text()
        girl_age = self.age.value()
        girl_district = self.district.currentText()
        service1_selected = self.service1.isChecked()
        service2_selected = self.service2.isChecked()
        service3_selected = self.service3.isChecked()
        service4_selected = self.service4.isChecked()
        service5_selected = self.service5.isChecked()
        safety_concern = self.yes_box.isChecked()
    
        # Check if no service is selected
        if not service1_selected and not service2_selected:
            self.error.setText("Please select a service needed")
            return  # Exit the function early since no service is selected
         
        # Clear any existing error message
        self.error.setText("")

        # Combine first and last names into a single variable
        self.girl_name = f"{girl_fname} {girl_lname}"

        # Create a list of selected services
        girl_services = []
        if service1_selected:
            girl_services.append("Medical Care")
        if service2_selected:
            girl_services.append("Education")
        if service3_selected:
            girl_services.append("Childcare")
        if service4_selected:
            girl_services.append("Counseling")
        if service5_selected:
            girl_services.append("Legal Services")
        
        # Create a Girl instance
        girl = Girl(self.girl_name, girl_age, girl_district, girl_services)

        # Call your matching algorithm
        self.best_center = find_best_placement(girl, centers)
        
        # Check for safety concern
        if safety_concern and self.best_center is not None:
            # Check if the district of the best center matches the girl's district
            if self.best_center.district == girl_district:
                # Remove the best center from the list of centers
                centers.remove(self.best_center)
                # Recalculate the best center after removing the original best center
                self.best_center = find_best_placement(girl, centers)
                
        # Calculate match score
        self.match_score = calculate_match_score(girl, self.best_center)
        
        # Information for victim database
        survivor_info = [girl_fname, girl_lname, girl_age, girl_district, self.best_center.name]
        self.cur.execute('INSERT INTO survivor_info (first_name, last_name, age, district, center ) VALUES (?,?,?,?,?)', survivor_info)
        
        # Commit and close the connection
        self.conn.commit()
        
        
        # Display match result
        match_result_text = f"Name: {self.girl_name}\nBest Placement: {self.best_center.name}\nScore: {self.match_score}"
        QMessageBox.information(self, "Match Result", match_result_text)

    def save_result(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Match Result", "", 
                                                   "Text Files (*.txt);;All Files (*)", 
                                                   options=options)

        if file_name:
            match_result_text = f"Name: {self.girl_name}\nBest Placement: {self.best_center.name}\nScore: {self.match_score}"
            try:
                with open(file_name, 'w') as file:
                    file.write(match_result_text)
                QMessageBox.information(self, "Save Successful", "Match result saved successfully.")
            except Exception as e:
                QMessageBox.warning(self, "Save Error", f"Error saving match result: {str(e)}")
            
    def display_center_statistics(self):
        # Read Placement Centers data from CSV file using pandas
        csv_file_path = "https://raw.githubusercontent.com/sharonjepkosgei/Empower_her/main/placement_centers_data.csv"
        centers = pd.read_csv(csv_file_path)
        # Extract names and ratings for plotting
        center_names = centers_df['Name'].tolist()
        ratings = centers_df['Rating'].tolist()
        
        # Create a Matplotlib widget
        matplotlib_widget = MatplotlibWidget(self)

        # Plotting
        fig = matplotlib_widget.canvas.figure
        ax = fig.add_subplot(111)
        ax.bar(center_names, ratings, color='tab:blue')
        ax.set_xlabel('Center Name')
        ax.set_ylabel('Rating')

        ax.set_title('Centers and Their Ratings')
        # Set tick positions and rotate the x-axis labels to a 45-degree angle
        ax.set_xticks(range(len(center_names)))
        ax.set_xticklabels(center_names, rotation=45, ha='right')

        # Add the Matplotlib widget to the layout
        self.layout().addWidget(matplotlib_widget)

        matplotlib_widget.canvas.draw()    
        

  
# main
app = QApplication(sys.argv)
mainwindow = WelcomeScreen()
widget = QtWidgets.QStackedWidget()
widget.addWidget(mainwindow)
widget.setFixedHeight(800)
widget.setFixedWidth(1200)
widget.show()
try:
    sys.exit(app.exec_())
except:
    print("Exiting")
                
                
    

