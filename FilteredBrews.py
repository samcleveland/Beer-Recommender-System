from kivymd.app import MDApp
from kivy.config import Config
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivymd.uix.label import MDLabel
from kivy.uix.image import AsyncImage
from kivymd.uix.list import TwoLineListItem
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from threading import Thread
import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
import random
from numpy import linalg as la
import time
import os


'''
The application code follows a general structure 

1. Screens  and Menus- controls the various screens the user will interact with
2. Buttons  - actions tied to specific button presses
3. Methods - additional methods that run in the background, and are not tied to somnething the user will interact with directly
4. Additional classes


Video link: https://youtu.be/y7i0nWwCUcQ

'''


cwd = os.getcwd()
cwd = '{}/Supporting Files'.format(cwd)

class RootWidget(GridLayout):
    'Class that handles root window'
    
    #set the default window size
    Window.size = (1200, 800)
    
    
    #Config.set('graphics', 'fullscreen', '0') #can be used to toggle fullsize screen
    Config.set('graphics', 'resizable', '0') #determines if the screen can be resized.  0 indicates no
    Config.write() #write settings
    

class Screen(FloatLayout):
    'class to handle GUI'
    def __init__(self, **kwargs):
        global cwd
        
        super(FloatLayout, self).__init__(**kwargs)      
        self.size = Window.size #set variable with current window size
        self.splash() #load splash screen 
        
        
        self.d = Data() #initialize class to import data
        Thread(target=self.d.read_file, daemon = True).start() #read beer file data
        
        self.UD = UserData() #import data of users reviews.  
        Thread(target=self.UD.load_data, daemon = True).start()
        
        self.lp = LoadProfiles() #initialize class to load user profiles
        self.lp.load() #load user profiles
        
        self.id = '' #initialize id varaible 
        self.copy_id = 'False' #initialize variable to determine if profile is copied from BeerAdvocate dataset.  If not false, will be int
        self.copy_toggle = 'False' #indicates True/False if variable is copied. 
        
        self.p = Profile(list(self.lp.profile.columns), self.id) #get user rating profile
        Thread(target=self.p.create, daemon = True).start() 

        self.Model = MatrixFactorization() #initialize initial model
        self.page = 0 #set starting page of review panel
        
        
    '''
    The next set of code is tied to screens within the application
    '''    
    
    def splash(self):
        'creates splash screen of program'
        self.layout = FloatLayout() #set layout type
        self.clear_screen() #clear all items on screen
        self.Enter = Button(text='Enter',
                            size = (100, 30),
                            pos = (self.size[0] * .5 - 50, self.size[1] * .1)) #adds button to enter application
        self.Enter.bind(on_press = self.login) #binds function to button
        self.add_widget(self.Enter) #add button to screen
        
        img_size = 2 * (self.size[1] // 3) #determine size of screen
        
        self.logo = AsyncImage(source='/'.join([cwd, 'Beer Labels copy White.jpg']), 
                        size = (img_size, img_size),
                        pos = (self.size[0] // 2 - img_size//2 , self.size[1]//2 - img_size//3)) #import logo
        
        self.add_widget(self.logo) #add image to screen
        
        
    #MENUS
    def menu(self):
        'creates initial menu where the user can select between create/login to account, review beers, or get recommendations'
        self.clear_screen() #clear current screen
        self.page = 0 #set starting page of review panel.  
        self.create_heading() #create menu buttons 
        
    def create_heading(self):
        'creates buttons on menu screen'
        self.CreateProfile = Button(text='Create Profile',
                    size = (self.size[0] //3, self.size[1] // 6),
                    pos = (self.size[0] //3, self.size[1] * .50))
        self.CreateProfile.bind(on_press = self.create)
        self.add_widget(self.CreateProfile)
        
        self.ReviewButton = Button(text='Review Beers',
                    size = (self.size[0] //3, self.size[1] // 6),
                    pos = (self.size[0] //3, self.size[1] * .30))
        self.ReviewButton.bind(on_press = self.reviews)
        self.add_widget(self.ReviewButton)
        
        self.GetRecommend = Button(text='Get Recommendation',
                    size = (self.size[0] //3, self.size[1] // 6),
                    pos = (self.size[0] //3, self.size[1] * .10))
        
        self.GetRecommend.bind(on_press = self.get_recommendation)
        
        self.add_widget(self.GetRecommend)
        
        self.banner = self.aimg = AsyncImage(source='/'.join([cwd, 'Beer Banner.jpg']), 
                                             size = (self.size[0], self.size[0]*.214),
                                    pos = (0, self.size[1] - self.size[0]*.214))
        
        self.add_widget(self.banner)
        
        
    def build_reviews(self):   
        'builds menu on the left side of the screen allowing the user to select beer for reviewing'
        self.font_size = self.size[1] // 60 #determine font size of text list on sidebar
        
        self.Next = Button(text='Next',
                           size = (100, 30),
                           pos = (500, 0))
        self.Next.bind(on_press = self.next_button) #button that advances to the next page of possible beers to review
        
        self.Previous = Button(text='Previous',
                               size = (100, 30),
                               pos = (400, 0))
        self.Previous.bind(on_press = self.previous_button) #button that advances to the previous page of possible beers to review
        
        self.add_return_button() #return to menu button
        
        self.add_widget(self.Next) #add buttons to screen
        self.add_widget(self.Previous) 
        
        bpp = 20 #number of beers per page
        
        beer_page = list(self.d.beers['beer/name'].iloc[bpp * self.page:bpp * (self.page+1)]) #create a list of beer names of all beers to be shown on the page
        beer_Id = list(self.d.beers['beer/beerId'].iloc[bpp * self.page:bpp * (self.page+1)]) #create a list of beer ids of all beers to be shown on the page
        
        #prints panel on left to select beers for reviewing
        for i in range(len(beer_page)):
            self.beer_list = TwoLineListItem(text = "[size={}]{}[/size]".format(self.font_size, beer_page[i]),
                                             secondary_text = "[size={}]Beer ID:{}[/size]".format(self.font_size // 2, beer_Id[i]),
                                             size = (self.size[0]//3, self.size[1] // bpp),
                                             pos = (0, self.size[1] * i//(bpp + 1))) #creates list elements 
            self.beer_list.bind(on_press = self.rate_beer) #action when clicked
            self.add_widget(self.beer_list) #adds list panel
            
    def create_menu(self):
        'create menu for creating/loading user profile'
        self.clear_screen() #deletes all elements on screen
        
        self.banner = self.aimg = AsyncImage(source='/'.join([cwd, 'Beer Banner.jpg']), 
                                     size = (self.size[0], self.size[0]*.214),
                            pos = (0, self.size[1] - self.size[0]*.214))
        
        self.add_widget(self.banner) #add banner image at top
        
        self.add_return_button() #return to menu button
        
        self.Create_Profile = Button(text='Create New Profile',
                               size = (self.size[0] // 4, 100),
                               pos = (30, 400))
        self.Create_Profile.bind(on_press = self.crt_prof_but)
        self.add_widget(self.Create_Profile) #button to create new profile
        
        self.Load_Profile = Button(text='Load Profile',
                               size = (self.size[0] // 4, 100),
                               pos = (30 , 200))
        self.Load_Profile.bind(on_press = self.load_prof_but)
        self.add_widget(self.Load_Profile) #button to load profile that was previously added by using the application.  Does not load data from training dataset
        
    def crt_prof_but(self, instance):
        'Response to button click when user wants to create a profile. Creates a menu for the user to enter desired username'

        self.clear_screen() #removes prior elements from screen
        self.create_menu() #creates menu buttons on the left side
        
        self.title = MDLabel(text = "Create a New Account",
                        color = [1,1,1,1],
                        font_style='H3',
                        halign="center",
                        size = (600, 50),
                        pos = (self.size[0] // 2 - 150, self.size[1]//2)) #adds title clarifying which option was selected
            
        self.add_widget(self.title) 
        
        self.profile_label = MDLabel(text = "Please enter a username:",
                        color = [1,1,1,1],
                        size = (300, 50),
                        pos = (self.size[0] // 2 - 150, self.size[1]*.3)) #adds instructions to enter username for new account
            
        self.add_widget(self.profile_label)
        
        self.enter_label = MDLabel(text = "Press the Enter key when desired username has been entered.",
                        color = [1,1,1,1],
                        font_style='Caption',
                        size = (600, 50),
                        pos = (self.size[0] // 2 - 150, self.size[1]*.15)) #instructions on how to submit selection
            
        self.add_widget(self.enter_label)
        
        self.crt_prof_input = TextInput(text='',
                                      multiline = False,
                                      size = (300, 50),
                                      pos = (self.size[0] // 2 + 75, self.size[1] * .3) )
        self.crt_prof_input.bind(on_text_validate=self.initialize_new_profile)
        
        self.add_widget(self.crt_prof_input) #text input area where user inputs username

        
 
        
        
    def create_new_profile(self, instance): 
        'checks if username is available and creates new account'
        try:
            self.remove_widget(self.new_name_label) #remove widget showing that username is not avaiable
        except:
            pass
        
        if self.account_name in self.lp.names: #check if username is already in use         
            self.new_name_label = MDLabel(text = "Username not available. Please enter a new name.",
                                color = [1,1,1,1],
                                theme_text_color = 'Secondary',
                                size = (300, 50),
                                pos = (self.size[0] // 2 - 150, self.size[1]*.225)) #label is the event that the username is not availlable 
            
            self.add_widget(self.new_name_label)
        
        else:
            self.clear_screen() #clear all elements from screen
            self.add_return_button() #add return to menu button
            
            self.create_menu() #add panel on left
            
            self.id = self.account_name #sets id equal to account name
            self.create_account() #print account created confirmation screen
            
    def load_prof_but(self, instance):
        'Creates screen for loading an account'
        self.clear_screen() #clears all elements from the screen
        
        self.create_menu() #create panel on left
        self.add_return_button() #add return to menu button
        
        self.title_label = MDLabel(text = "Load Account",
                color = [1,1,1,1],
                font_style = 'H3',
                halign="center",
                size = (600, 50),
                pos = (self.size[0] // 2 - 150, self.size[1] * .5)) #adds title clarifying what page is for
            
        self.add_widget(self.title_label)
        
        self.profile_label = MDLabel(text = "Please enter a username:",
                color = [1,1,1,1],
                size = (300, 50),
                pos = (self.size[0] // 2 - 150, self.size[1] * .3)) #prompts user to input their username
            
        self.add_widget(self.profile_label)
        
        self.enter_label = MDLabel(text = "Press the Enter key when desired username has been entered.",
                color = [1,1,1,1],
                font_style = 'Caption',
                size = (600, 50),
                pos = (self.size[0] // 2 - 150, self.size[1] * .15)) #instructions on how to submit username
            
        self.add_widget(self.enter_label)
        
        self.load_prof_input = TextInput(text='',
                                      multiline = False,
                                      size = (300, 50),
                                      pos = (self.size[0] // 2 + 75, self.size[1] * .3) )
        self.load_prof_input.bind(on_text_validate=self.load_prof_action) #area for user to input username
        
        self.add_widget(self.load_prof_input)
        
        
        
    def create_account(self):
        'Screen confirming account was created'
        self.new_account_label = MDLabel(text = "Account {} created.".format(self.id),
                            color = [1,1,1,1],
                            size = (300, 50),
                            pos = (self.size[0] // 2, self.size[1] * .75)) #confirms usernbame of new account
        
        self.add_widget(self.new_account_label)
        
        self.p = Profile(list(self.lp.profile.columns), self.id) #generates profile
        Thread(target=self.p.create, daemon = True).start()
        
        self.copy_prof_but(None)  #calls next screen asking if user would like to steal another persons reviews
        
    def load_prof_action(self, instance):
        
        if instance.text in list(self.lp.names):
            self.id = instance.text
            idx = self.lp.names.index(instance.text)
            self.p.profile = np.array(self.lp.profile.iloc[idx].values)
            self.copy_toggle = self.lp.duplicate[idx]
            self.p.profile = self.p.profile.reshape(1, len(self.p.profile))
        
            
            self.remove_widget(self.load_prof_input)
            self.remove_widget(self.profile_label)
            
            self.profile_analysis()
        else:
            self.create_new_prof(instance.text)
                        

    def profile_analysis(self):
        'Creates screen analyzing how the loaded profile has rated beers'
        self.p.analysis() #run method to analyze profile in Profile class
        
        self.clear_screen() #clear current screen
        
        self.banner = self.aimg = AsyncImage(source='/'.join([cwd, 'Beer Banner.jpg']), 
                                         size = (self.size[0], self.size[0]*.214),
                                         pos = (0, self.size[1] - self.size[0]*.214)) #add banner
        
        self.add_widget(self.banner) 
        
        self.add_return_button() #add return to menu button
        
        self.load_new_label = MDLabel(text = "{}".format(self.id),
                        markup = True,
                        font_style = 'H2',
                        halign='center',
                        color = [0,0,0,0],
                        size = (500,25),
                        pos = (self.size[0] // 2 - 75, self.size[1]//2 + 75)) #add user profile at top
        
        self.add_widget(self.load_new_label)
        
        self.rate1 = MDLabel(text = "[size=16]Beers scored as a 1: {}[/size]".format(self.p.df1[0]),
                        markup = True,
                        color = [0,0,0,0],
                        size = (500,25),
                        pos = (self.size[0] // 2 - 75, self.size[1]//2)) #number of beers rated between 1 and 2
        
        self.add_widget(self.rate1)
        
        self.rate2 = MDLabel(text = "[size=16]Beers scored as a 2: {}[/size]".format(self.p.df2[0]),
                        markup = True,
                        color = [0,0,0,0],
                        size = (500,25),
                        pos = (self.size[0] // 2 - 75, self.size[1]//2 - 50)) #number of beers rated between 2 and 3
         
        self.add_widget(self.rate2)
        
        self.rate3 = MDLabel(text = "[size=16]Beers scored as a 3: {}[/size]".format(self.p.df3[0]),
                        markup = True,
                        color = [0,0,0,0],
                        size = (500,25),
                        pos = (self.size[0] // 2 - 75, self.size[1]//2 - 100)) #number of beers rated between 3 and 4
        
        self.add_widget(self.rate3)
        
        self.rate4 = MDLabel(text = "[size=16]Beers scored as a 4: {}[/size]".format(self.p.df4[0]),
                        markup = True,
                        color = [0,0,0,0],
                        size = (500,25),
                        pos = (self.size[0] // 2 - 75, self.size[1]//2 - 150)) #number of beers rated between 4 and 5
        
        self.add_widget(self.rate4)

        self.rate5 = MDLabel(text = "[size=16]Beers scored as a 5: {}[/size]".format(self.p.df5[0]),
                        markup = True,
                        color = [0,0,0,0],
                        size = (500,25),
                        pos = (self.size[0] // 2 - 75, self.size[1]//2 - 200)) #number of beers rated as 5
        
        self.add_widget(self.rate5)   

        self.rate_total = MDLabel(text = "[size=20]Total Reviewed Beers: {}[/size]".format(self.p.df_total[0]),
                        markup = True,
                        color = [0,0,0,0],
                        size = (500,25),
                        pos = (self.size[0] // 2 - 75, self.size[1]//2 - 250)) #total number of beers rated
        
        self.add_widget(self.rate_total)  

        self.ReviewButton = Button(text='Review Beers',
                    size = (self.size[0]//4, 100),
                    pos = (30, 400))
        self.ReviewButton.bind(on_press = self.reviews)  #add button to take user to beer review screen 
        self.add_widget(self.ReviewButton)          
        
        self.RecommendButton = Button(text='Recommend Beers',
                    size = (self.size[0]//4, 100),
                    pos = (30, 200))
        self.RecommendButton.bind(on_press = self.get_recommendation) #add button to take user to beer recommender screen
        self.add_widget(self.RecommendButton)       
        
   
    def create_new_prof(self, account_name):
        'Screen that informs the user that the requested profile is not available for loading.  Ask if user would like to create account instead'
        self.clear_screen() #clears screen
        
        self.create_menu() #recreates screen
        
        self.account_name = account_name 
        
        self.load_new_label = MDLabel(text = "[size=20]Profile {} not found.\n\nWould you like to create this profile?[/size]".format(self.account_name),
                                markup = True,
                                color = [0,0,0,0],
                                halign = 'center',
                                size = (500,25),
                                pos = (self.size[0] // 2 - 150, self.size[1] * .5)) #asks user if they would like to create new profile with this name
        
        self.add_widget(self.load_new_label)
        
        self.create_yes = Button(text='Yes',
                size = (150, 30),
                pos = (self.size[0]//2 - 100, self.size[1]*.3))
        self.create_yes.bind(on_press = self.create_new_profile) #yes button
        self.add_widget(self.create_yes)
        
        self.create_no = Button(text='No',
                    size = (150, 30),
                    pos = (self.size[0] // 2 + 150, self.size[1]*.3))
        self.create_no.bind(on_press = self.copy_no_but) #no button
        self.add_widget(self.create_no)


    def copy_prof_but(self, instance):
        'Screen asking the user if they would like to copy a random profile from the training data.  This is a quick way to sample the recommender functionality without developing a complete profile'
        self.create_menu() #create menu of left side of screen
        
        self.random_label = MDLabel(text = "Would you like to copy the beer ratings from a random account?  Copying a random profile will override your current ratings with the ratings of another random user.\n\nThis cannot be reversed.\n\nWould you like to proceed?",
                color = [1,1,1,1],
                halign = 'center',
                size = (500, 150),
                pos = (self.size[0] // 2 - 150, self.size[1]*.45)) #ask user if they would like to copy another profile
            
        self.add_widget(self.random_label)
        
        self.copy_yes = Button(text='Yes',
                    size = (150, 30),
                    pos = (self.size[0] // 2 - 100, self.size[1]*.3))
        self.copy_yes.bind(on_press = self.copy_yes_but)
        self.add_widget(self.copy_yes) #yes button
        
        self.Copy_no = Button(text='No',
                    size = (150, 30),
                    pos = (self.size[0] // 2 + 150, self.size[1]*.3))
        self.Copy_no.bind(on_press = self.copy_no_but)
        self.add_widget(self.Copy_no) #no button
    
    def rate_beer(self, instance): 
        'Create screen for rating beers'
        self.clear_screen() #clears screen
        self.build_reviews() #adds review panel
        
        try:
            self.remove_widget(self.aimg) #remove BA image
        except:
            pass 
        
        self.beer_id = instance.secondary_text.split(':')[1].split('[')[0] #get beerid from beer label
        self.brewerId = self.d.beers[self.d.beers['beer/beerId'] == int(self.beer_id)]['beer/brewerId'] #loo up brewer id
        
        self.beer_idx = self.UD.beer_list.index(int(self.beer_id)) #set index of beer 
        
        self.BA_labels() #print beer advocate labels 

        
        #do requests first to determine if page exists
        self.image = 'https://cdn.beeradvocate.com/im/beers/{}.jpg'.format(self.beer_id)
        
        #check if photo exists
        if requests.get(self.image).status_code != 200:
            self.image = 'https://cdn.beeradvocate.com/im/placeholder-beer.jpg'
            
        self.aimg = AsyncImage(source=self.image, 
                        size = (400, 400),
                        pos = (self.size[0] *.50 , self.size[1] * .52)) #add image to screen
        
        self.add_widget(self.aimg)
        
        self.citation = MDLabel(text = "[size=8]Citation for photo: {}[/size]".format(self.image),
                        markup = True,
                        color = [0,0,0,0],
                        size = (500,25),
                        pos = (self.size[0] // 2 + 125, 0)) #add citation to screen
        
        self.add_widget(self.citation)

    
        self.review_input = TextInput(text='Enter your review (1-5)',
                                      multiline = False,
                                      size = (200, 40),
                                      pos = (self.size[0] // 2 + 100, self.size[1]//2 - 290) )
        self.review_input.bind(on_text_validate=self.submit) #allow user to input score
        
        self.add_widget(self.review_input)
        
        if self.p.profile[:,self.beer_idx] > 0: #check if user has scored beer previously
            self.current_score_lab = MDLabel(text = 'My Score: {}'.format(self.p.profile[:,self.beer_idx][0]),
                                    font_size = '12sp',
                                    color = [1,1,1,1],
                                    size = (300, 100),
                                    pos = (self.size[0] // 2, self.size[1]//2 - 225)) #print users current score
        else:
            self.current_score_lab = MDLabel(text = 'My Score: Not Yet Rated',
                        font_size = '20sp',
                        color = [1,1,1,1],
                        size = (300, 100),
                        pos = (self.size[0] // 2, self.size[1]//2 - 225)) #print no score
            

        self.add_widget(self.current_score_lab)
        
    def model_load_screen(self):
        'Screen to show that model will take time to load'
        self.clear_screen() #clear screen
        self.banner = self.aimg = AsyncImage(source='/'.join([cwd, 'Beer Banner.jpg']), 
                                     size = (self.size[0], self.size[0]*.214),
                            pos = (0, self.size[1] - self.size[0]*.214))
        
        self.add_widget(self.banner)
        
        self.add_return_button() #add return to menu button
    
        self.model_lab = MDLabel(text = '{} will take time to analyze your taste profile.\n\nWould you like to proceed?'.format(self.Model.Name),
                font_size = '12sp',
                color = [1,1,1,1],
                halign = 'center',
                size = (self.size[0], 100),
                pos = (0, self.size[1]//2)) #print label that model is loading
        
        self.add_widget(self.model_lab)
        
        self.model_yes = Button(text='Yes',
                    size = (150, 30),
                    pos = (self.size[0] // 2 - 200, self.size[1]*.3))
        self.model_yes.bind(on_press = self.start_item)
        self.add_widget(self.model_yes) #yes button
        
        self.model_no = Button(text='No',
                    size = (150, 30),
                    pos = (self.size[0] // 2 + 50, self.size[1]*.3))
        self.model_no.bind(on_press = self.copy_no_but)
        self.add_widget(self.model_no) #no button
        
    def user_model_load_screen(self):
        'Screen to show that model will take time to load'
        self.clear_screen() #clear screen
        self.banner = self.aimg = AsyncImage(source='/'.join([cwd, 'Beer Banner.jpg']), 
                                     size = (self.size[0], self.size[0]*.214),
                            pos = (0, self.size[1] - self.size[0]*.214))
        
        self.add_widget(self.banner)
        
        self.add_return_button() #add return to menu button
    
        self.model_lab = MDLabel(text = '{} will take a very long time to analyze your taste profile.\n\nWould you like to proceed?'.format(self.Model.Name),
                font_size = '12sp',
                color = [1,1,1,1],
                halign = 'center',
                size = (self.size[0], 100),
                pos = (0, self.size[1]//2)) #print label that model is loading
        
        self.add_widget(self.model_lab)
        
        self.model_yes = Button(text='Yes',
                    size = (150, 30),
                    pos = (self.size[0] // 2 - 200, self.size[1]*.3))
        self.model_yes.bind(on_press = self.start_user)
        self.add_widget(self.model_yes) #yes button
        
        self.model_no = Button(text='No',
                    size = (150, 30),
                    pos = (self.size[0] // 2 + 50, self.size[1]*.3))
        self.model_no.bind(on_press = self.copy_no_but)
        self.add_widget(self.model_no) #no button
            
    
        
    def item_based_screen(self):
        'Screen showing results of item based recommender'
        self.clear_screen() #clear prior screen
        self.add_return_button() #add return to menu button
    
        if self.copy_toggle != 'False': #add matrix factorization button
            
            self.MF_button = Button(text='Filtered Brews Recommendation',
                        size = (300, 40),
                        pos = (self.size[0] * .2, self.size[1] * .90))
            self.MF_button.bind(on_press = self.jump_to_MF)
            self.add_widget(self.MF_button)
        
        self.user_rec_button = Button(text='User Based Recommendation',
                    size = (300, 40),
                    pos = (self.size[0] * .55, self.size[1] * .90))
        self.user_rec_button.bind(on_press = self.user_based_rec)
        self.add_widget(self.user_rec_button) #add user based recommendation button
        
        self.print_results(self.Model.final_list) #call method to add results to screen
        
        
    def user_based_screen(self):
        'Screen showing results of item based recommender'
        self.clear_screen() #clear prior screen
        self.add_return_button() #add return to menu button
    
        if self.copy_toggle != 'False': #add matrix factorization button
            
            self.MF_button = Button(text='Filtered Brews Recommendation',
                        size = (300, 40),
                        pos = (self.size[0] * .2, self.size[1] * .90))
            self.MF_button.bind(on_press = self.jump_to_MF)
            self.add_widget(self.MF_button)
        
        self.item_rec_button = Button(text='Item Based Recommendation',
                    size = (300, 40),
                    pos = (self.size[0] * .55, self.size[1] * .90))
        self.item_rec_button.bind(on_press = self.item_based_rec)
        self.add_widget(self.item_rec_button) #add user based recommendation button
        
        self.print_results(self.Model.final_list) #call method to add results to screen
        
    def print_results(self, beer_list):
        'Adds the models 3 best beers to the screen'
        idx = 0
        
        for beer in beer_list: #loop through top 3 beers
            width = self.size[0] // len(beer_list) #determine width of each colum
            beer_id = self.UD.beer_list[beer[0]] #get beer id
            brewerId = list(self.d.beers[self.d.beers['beer/beerId'] == int(beer_id)]['beer/brewerId'])[0] #determine brewer id
            
            self.BA_MF = BeerAdvocate(beer_id, brewerId) #initialize BA class
            self.BA_MF.get_details() #get beer deteails
            
            
            self.load_new_label = MDLabel(text = "{}".format(self.Model.Name),
                        markup = True,
                        font_style = 'H2',
                        halign='center',
                        color = [0,0,0,0],
                        size = (self.size[0],25),
                        pos = (0, self.size[1]//2 + 250)) #add user profile at top
        
            self.add_widget(self.load_new_label)
            
            


            
            #do requests first to determine if page exists
            self.image = 'https://cdn.beeradvocate.com/im/beers/{}.jpg'.format(beer_id) #get image of beer 
            
            #check if photo exists, otherwise get placeholder beer
            if requests.get(self.image).status_code != 200:
                self.image = 'https://cdn.beeradvocate.com/im/placeholder-beer.jpg' 
                
            self.aimg = AsyncImage(source=self.image, 
                            size = (200, 200),
                            pos = (self.size[0] *.1 + idx * width  , self.size[1] * .5)) #create place for image of beer
            
            self.add_widget(self.aimg)
            
            
            self.name_lab = MDLabel(text = 'Name: {}'.format(self.BA_MF.name),
                            font_size = '12sp',
                            color = [1,1,1,1],
                            size = (200, 100),
                            pos = (self.size[0] *.1 + idx * width, self.size[1]//2 - 75)) #add name
            
            self.add_widget(self.name_lab)
            
            self.brewery_lab = MDLabel(text = 'Brewery: {}'.format(self.BA_MF.brewery),
                    font_size = '12sp',
                    color = [1,1,1,1],
                    size = (200, 100),
                    pos = (self.size[0] *.1 + idx * width, self.size[1]//2 - 125)) #add brewery
    
            self.add_widget(self.brewery_lab)       
            
            self.country_lab = MDLabel(text = 'Location: {}'.format(self.BA_MF.country),
                            font_size = '12sp',
                            color = [1,1,1,1],
                            size = (200, 100),
                            pos = (self.size[0] *.1 + idx * width, self.size[1]//2 - 175)) #add country
            
            self.add_widget(self.country_lab)
            
            self.style_lab = MDLabel(text = 'Style: {}'.format(self.BA_MF.style),
                    font_size = '12sp',
                    color = [1,1,1,1],
                    size = (200, 100),
                    pos = (self.size[0] *.1 + idx * width, self.size[1]//2 - 225)) #add style
    
            self.add_widget(self.style_lab)
            
            self.expected_lab = MDLabel(text = 'Predicted Score: %.2f' % beer[1],
                    font_size = '12sp',
                    color = [1,1,1,1],
                    size = (200, 100),
                    pos = (self.size[0] *.1 + idx * width, self.size[1]//2 - 275)) #add predicted score
    
            self.add_widget(self.expected_lab)
            
            self.citation = MDLabel(text = "[size=8]Citation for photo: {}[/size]".format(self.image),
                            markup = True,
                            color = [0,0,0,0],
                            size = (width * .4, 25),
                            pos = (self.size[0] *.1 + idx * width, 0)) #add citation of image
            
            self.add_widget(self.citation)
            
            idx += 1
            
    def BA_labels(self):
        'Get labels from beer advocate.com for recommendation screen'
        self.BA = BeerAdvocate(self.beer_id, list(self.brewerId)[0]) #start class
        self.BA.start() 
        self.BA.get_details() #get details
        
        #add labels to screen
        self.name_lab = MDLabel(text = 'Name: {}'.format(self.BA.name),
                        font_size = '12sp',
                        color = [1,1,1,1],
                        size = (300, 100),
                        pos = (self.size[0] // 2, self.size[1]//2 - 25))
        
        self.add_widget(self.name_lab)
        
        self.brewery_lab = MDLabel(text = 'Brewery: {}'.format(self.BA.brewery),
                font_size = '12sp',
                color = [1,1,1,1],
                size = (300, 100),
                pos = (self.size[0] // 2, self.size[1]//2 - 75))

        self.add_widget(self.brewery_lab)       
        
        self.country_lab = MDLabel(text = 'Location: {}'.format(self.BA.country),
                        font_size = '12sp',
                        color = [1,1,1,1],
                        size = (300, 100),
                        pos = (self.size[0] // 2, self.size[1]//2 - 125))
        
        self.add_widget(self.country_lab)
        
        self.style_lab = MDLabel(text = 'Style: {}'.format(self.BA.style),
                font_size = '12sp',
                color = [1,1,1,1],
                size = (300, 100),
                pos = (self.size[0] // 2, self.size[1]//2 - 175))

        self.add_widget(self.style_lab)

           
        
        
    
    '''
    Code in this section represent code tied to handling specific button processes
    '''
    
    def initialize_new_profile(self, instance):
        'initializes the process to create a new profile based on the user name input by user'
        self.account_name = instance.text #sets input name as account name
        self.create_new_profile(instance)
        
    def copy_yes_but(self, instance):
        'Updates user profile to reflect random profile from training set'
        try:
            new_id = random.randint(0, len(self.UD.customer_list)-1) #get random number 
            profile = self.UD.beer_mat.iloc[new_id].values #get new ratings 
            self.p.profile = np.array(profile).reshape((1, len(profile))) #reformat ratings as array
            
            self.profile_analysis() #analyze portfolio
            self.copy_id = new_id
            self.copy_toggle = new_id
        except AttributeError:
            time.sleep(.25)
            self.copy_yes_but(instance)
    
    def copy_no_but(self, instance):
        'Does not copy a random profile over a user profile'
        self.menu()
        self.copy_id = 'False'
        self.copy_toggle = 'False'
        
    def Pass_button(self, instance):
        'Button that does nothing'
        pass
    
        
    def next_button(self, instance):
        'advance to next page of beers'
        self.page += 1
        self.reviews(instance)
        
    def previous_button(self, instance):
        'go to previous page of beers'
        if self.page > 0:
            self.page -= 1      
        self.reviews(instance)
        
        
    def clear_screen(self):
        'Removes all widgets from the screen except the exit button'
        self.clear_widgets() #deletes widgets
        
        self.Exit = Button(text='Exit',
                    size = (150, 30),
                    pos = (self.size[0] - 150, 0))
        self.Exit.bind(on_press = self.exit_button) #re add exit button
        self.add_widget(self.Exit)
        
    def exit_button(self, instance):
        'exit program when run'
        self.lp.append(self.p.profile, self.id, self.copy_toggle)
        self.lp.save() #save profile to csv prior to exiting
        
        exit()
        
    def add_return_button(self):
        'Button to return to menu screen'        
        self.ReturnMenu = Button(text='Menu',
                       size = (100, 30),
                       pos = (self.size[0] - 100, self.size[1]-30)) 
        self.ReturnMenu.bind(on_press = self.enter_button)
        self.add_widget(self.ReturnMenu)
        

    '''
    Methods in this section are tied to specific actions
    '''

    def create(self, instance):
        'Create a profile to save reviews'
        self.create_menu()
    
    def recommend(self):
        'determine which recommend system to default to'
        try:
            self.clear_screen()
            self.add_return_button()
        
            #self.UB.set_var(self.UD.beer_mat, self.p.profile)
            if self.copy_toggle != "False":
                self.jump_to_MF() #matrix factorization
                
            else:
                self.item_based_rec() #item based 
        except AttributeError:
            time.sleep(.5)
            self.recommend()
                

    def item_based_rec(self, instance = None):
        'Initialize Item based recommender'
        self.clear_screen() #clears screen
        self.add_return_button() #button to return to menu
        self.Model = ItemBased() #initialize class
        
        self.model_load_screen() #initialize loading screen
        
    def user_based_rec(self, instance = None):
        'Initialize Item based recommender'
        self.clear_screen() #clears screen
        self.add_return_button() #button to return to menu
        self.Model = UserBased() #initialize class
        
        self.user_model_load_screen() #initialize loading screen
        
        
    def start_item(self, instance = None):
        'Initiale thread for Item based recommender'
        self.clear_screen()
        
        self.Model = ItemBased() #initialize class
        self.t1 = Thread(target=self.Model.recommend, args = [self.p.profile], daemon = True) #create thread
        self.t1.start() #start thread
        self.t1.join() #return results
        self.item_based_screen() #go to print screen
        
    def start_user(self, instance = None):
        'Initiale thread for Item based recommender'
        self.clear_screen()
        
        self.Model = UserBased() #initialize class
        self.t1 = Thread(target=self.Model.recommend, args = [self.UD.beer_mat, self.p.profile, self.copy_toggle], daemon = True) #create thread
        self.t1.start() #start thread
        self.t1.join() #return results
        self.user_based_screen() #go to print screen
        

        
    def jump_to_MF(self, N = 3):
        'Method to initialize Matrix facotrization model'
        self.clear_screen() #clear screen
        self.add_return_button() #add return to menu button
        
        self.Model = MatrixFactorization() #initialize class
        self.Model.setvars(self.UD.beer_mat, self.p.profile, self.UD.beer_list, self.copy_toggle, list(np.nonzero(self.p.profile)[1])) #set variable for class
        
        self.Model_thread = Thread(target=self.Model.recommendation, daemon = True) #create thread
        self.Model_thread.start() #start thread
        time.sleep(.5) #sleep to give the model time to run
        
        self.user_rec_button = Button(text='User Recommendation',
                    size = (300, 40),
                    pos = (self.size[0] * .2, self.size[1] * .90))
        self.user_rec_button.bind(on_press = self.user_based_rec)
        self.add_widget(self.user_rec_button) #add user rec button
        
        self.item_rec_button = Button(text='Item Recommendation',
                    size = (300, 40),
                    pos = (self.size[0] * .55, self.size[1] * .90))
        self.item_rec_button.bind(on_press = self.item_based_rec)
        self.add_widget(self.item_rec_button) #add item rec button
        
        beer_list = self.Model.final_list[:3] #get 3 best beers
        
        self.print_results(beer_list) #print results to screen
        
    def reviews(self, instance):
        'prints list for user to select beers to review'
        self.clear_screen()
        self.build_reviews()
        
    def submit(self, instance):
        'process user review submission'
        try:
            self.remove_widget(self.label) #try to remove confirmation of submission from prior submission
        except:
            pass
        
        try:
             score = float(instance.text) #convert score to float
                
             if score >= 1 and score <= 5: #if score is betwenn 1 and 5
                self.label = MDLabel(text = "Thank you for your submission",
                        font_size = '12sp',
                        color = [0,0,0,0],
                        size = (300, 100),
                        pos = (self.size[0] // 2 + 100, self.size[1]//2 - 350)) #print confirmation of submission 
                
                self.p.update(self.beer_idx, score) #update user profile
                
             else:
                self.label = MDLabel(text = "Please enter a number 1-5",
                        font_size = '12sp',
                        color = [1,1,1,1],
                        size = (300, 100),
                        pos = (self.size[0] // 2 + 100, self.size[1]//2 - 350)) #print response
      
        except:
            self.label = MDLabel(text = "Please enter a number 1-5",
                                    font_size = '12sp',
                                    color = [1,1,1,1],
                                    size = (300, 100),
                                    pos = (self.size[0] // 2 + 100, self.size[1]//2 - 350)) #print response
            
        self.add_widget(self.label)
        
    def enter_button(self, instance):
        'Clear screen and move to menu'
        time.sleep(.5)
        self.menu()
        
    def login(self, instance):
        'process login'
        self.create_menu()
        
    def get_recommendation(self, instance):
        'process recommendation button'
        self.clear_screen()
        self.recommend()


class MyApp(MDApp): #switch this back to App if removing MDApp for list

    def build(self):
        'builds screen'
        root = RootWidget()
        s = Screen()
        root.add_widget(s)
        self.title = 'Filtered Brews'
        self.theme_cls.primary_palette = "Green"
        return root
    

    
class Data():
    'class to get data on beers included in model'
    def __init__(self):
        global cwd
        self.filename = '/'.join([cwd,'IPA_names.csv'])
        self.beers = pd.DataFrame()
        
        
    def read_file(self):
        'reads names beers'
        self.beers = pd.read_csv(self.filename)
        
class BeerAdvocate(Thread):
    'class to get data from beeradvocate.com'
    def __init__(self, beerId, brewerId):
        Thread.__init__(self)
        self.url = 'https://www.beeradvocate.com/beer/profile/{}/{}/'.format(brewerId, beerId)
        
    def get_details(self):
        'scrape beer data from website'
        try:
            r = requests.get(self.url)
        
            r_text = r.text
            
            soup = BeautifulSoup(r_text, 'html.parser')
            
            s_t = soup.get_text().strip()
            
            s_t_list = s_t.split('\n')
            
            from_index = s_t_list.index('From:')
            self.brewery = s_t_list[from_index + 1]
            self.country = s_t_list[from_index + 3]
            
            style_index = s_t_list.index('Style:')
            self.style = s_t_list[style_index + 1]
            self.name = s_t_list[0].split('|')[0].strip()
        except:
            self.brewery = 'Page Not Found'
            self.country = 'Page Not Found'
            self.style = 'Page Not Found'
            self.name = 'Page Not Found'
            
            
class LoadProfiles():
    'Loads profiles from accounts created through app'
    def load(self):
        'load data'
        global cwd
        self.profile = pd.read_csv('/'.join([cwd,'User_ratings.csv']), header = None) #get ratings
        self.names = list(pd.read_csv('/'.join([cwd,'Usernames.csv']), header = None)[0]) #get username
        self.duplicate = list(pd.read_csv('/'.join([cwd,'Duplicated.csv']), header = None)[0]) #checks if account has been duplicated from training data
        
    def append(self, current_profile, user_id, copy_id):  
        'add item reviews to database'
        if user_id in self.names: #check if user already exists
            idx = self.names.index(user_id)
            self.profile.iloc[idx] = current_profile.T.reshape((len(current_profile.T,)))
            self.duplicate[idx] = copy_id
        else:
            self.profile = self.profile.append(pd.DataFrame(current_profile, columns = self.profile.columns))
            self.names.append(user_id)
            self.duplicate.append(copy_id)
    
    def save(self):
        'Save dataset'
        global cwd
        self.profile.to_csv('/'.join([cwd,'User_ratings.csv']), index = False, header = False)
        pd.DataFrame(self.names, columns = ['username']).to_csv('/'.join([cwd,'Usernames.csv']), index = False, header = False)
        pd.DataFrame(self.duplicate).to_csv('/'.join([cwd,'Duplicated.csv']), index = False, header = False)
        
class Profile():
    'Class that handles user ratings'
    def __init__(self, beer_list, user_id):
        global cwd
        self.beer_list = beer_list
        self.user_id = user_id
    
    def create(self):
        'create starting user profile'
        self.profile = np.zeros((1, len(self.beer_list)))
        
    def analysis(self):
        'get breakdown of current scores'
        self.df = pd.DataFrame(self.profile.T)
        self.df1 = self.df[(self.df[0] >=1) & (self.df[0] <2)].count() 
        self.df2 = self.df[(self.df[0] >=2) & (self.df[0] <3)].count() 
        self.df3 = self.df[(self.df[0] >=3) & (self.df[0] <4)].count() 
        self.df4 = self.df[(self.df[0] >=4) & (self.df[0] <5)].count() 
        self.df5 = self.df[(self.df[0] == 5)].count() 
        self.df_total = self.df[self.df[0] > 0].count()

    def update(self, beer_idx, score):
        'update score'
        self.profile[:, beer_idx] = score    

class UserData(Thread):
    def __init__(self):
        Thread.__init__(self)
    
    def load_data(self):
        global cwd
        self.beer_list = list(pd.read_csv('/'.join([cwd,'IPA_beers.csv']), header=None)[0])
        self.customer_list = list(pd.read_csv('/'.join([cwd,'IPA_profiles.csv']), header=None, na_values = '')[0])
        self.beer_mat = pd.read_csv('/'.join([cwd,'IPA_mat.csv']), header=None)
        
class UserBased(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.Name = 'User Based'
        self.simMat = np.mat(np.empty((0,0)))
        self.final_list = []
        
    def load(self):
        print('loading simMat')
        self.simMat = np.loadtxt('/'.join([cwd,'user_based_sim.csv']),delimiter=',')
    
    def euclidSim(inA,inB):
        return 1.0 / (1.0 + la.norm(inA - inB))
    
    def pearsonSim(inA,inB):
        if len(inA) < 3 : return 1.0
        return 0.5 + 0.5 * np.corrcoef(inA, inB, rowvar = 0)[0][1]
    
    def cosineSim(inA,inB):
        num = float(inA.T * inB)
        denom = la.norm(inA)*la.norm(inB)
        return 0.5 + 0.5 * (num / denom)
    
    def estimate(self, item, k = 5):
        'get user based recommendation score'
        count = 0
        total_sim = 0.0
        rating = 0.0
        
        sorted_list = list(enumerate(self.simMat))
        sorted_list = sorted(sorted_list, key=lambda x: x[1], reverse=True)
        
        for usr in sorted_list:
            usr_idx = usr[0]
            
            if count >= k:
                return self.return_rate(rating, total_sim)
            
            if self.data[usr_idx, item] != 0:
                score = self.data[usr_idx, item]
                sim = self.simMat[usr_idx]
                total_sim += sim
                rating += score * sim
                count += 1
                
        return self.return_rate(rating, total_sim)     
    
    def filter_simMat(self):
        simMat = np.loadtxt('/'.join([cwd,'user_based_sim.csv']),delimiter=',')
        
        self.simMat = simMat[int(self.user_id), :]

        
    
    def return_rate(self, rating, total_sim):
        'return rating'
        if total_sim == 0:
            return 0
        else:
            return rating / total_sim
            
    
    def recommend(self, data, user, user_id, N=3):    
        'get recommended beers'
        self.user_id = user_id
        self.data = np.mat(data)
        self.user = np.mat(user)
        
        print('getting recommendation')
        
        if self.user_id == 'False':
            self.getSim()
        else:
            self.filter_simMat()
        
        unratedItems = np.nonzero(self.user.A==0)[1] #find unrated items 
        if len(unratedItems) == 0: return 'you rated everything'
        itemScores = []
        for item in unratedItems:
            estimatedScore = self.estimate(item)
            itemScores.append((item, estimatedScore))
        self.final_list = sorted(itemScores, key=lambda jj: jj[1], reverse=True)[:N]
        
        print('UB recommendation done')
        
    
    def getSim(self, metric = euclidSim):
        'create simiarlity matrix'
        print('creating simMat')
        self.dataMat = np.mat(self.data)
        self.userMat = np.mat(self.user)
                
        self.simMat = np.ones((len(self.dataMat),1))
        self.UB_results = []
        
        for user in range(len(self.dataMat)):
            ind = np.nonzero(np.logical_and(self.dataMat[user,:]>0,self.userMat>0))[1]
            
            if len(ind) == 0:
                sim = 0
            else:
                array1 = np.take(self.dataMat[user,:], ind).T
                array2 = np.take(self.userMat, ind).T
                sim = metric(array1, array2)

            self.simMat[user] = sim
            
        print('similarity measured')
        
        #self.recommend()
        
    def set_var(self, data, user):
        'set class variables'
        self.data = data
        self.user = user
        
        
class ItemBased(Thread):   
    def __init__(self):
        'Item based recommmendation system'
        Thread.__init__(self)
        self.final_list = []
        self.Name = 'Item Based Model'
        
        
    def estimate(self, item, sim):
        'get estimated score'
        count = 0
        total_sim = 0.0
        rating = 0.0
        k = 5 #size of neighborhood
        
        sorted_list = list(enumerate(np.array(sim)[item]))
        sorted_list = sorted(sorted_list, key=lambda x: x[1], reverse=True)
        
        for beer in sorted_list:
            beer_idx = beer[0]
            
            if count >= k:
                return self.return_rate(rating, total_sim)
            
            if beer_idx != item and self.dataMat[0, beer_idx] != 0:
                score = self.dataMat[0, beer_idx]
                sim_score = sim[item, beer_idx]
                total_sim += sim_score
                rating += score * sim_score
                count += 1
                
        return self.return_rate(rating, total_sim)
    
    def return_rate(self, rating, total_sim):
        'calculates score'
        if total_sim == 0:
            return 0
        else:
            return rating / total_sim
        
    def recommend(self, user, N=3):
        'get top 3 unrated beers'
        self.dataMat = user
        
        print('running Item Based model, please be patient')
        sim = np.loadtxt('/'.join([cwd,'Item_SVD_sim.csv']),delimiter=',')
        
        unratedItems = np.nonzero(self.dataMat==0)[1] #find unrated items 
        if len(unratedItems) == 0: return 'you rated everything'
        itemScores = []
        for item in unratedItems:
            estimatedScore = self.estimate(item, sim)
            itemScores.append((item, estimatedScore))
        self.final_list = sorted(itemScores, key=lambda jj: jj[1], reverse=True)[:N]
        print('Item Based model complete')
        

    
    
class MatrixFactorization(Thread):
    'Matrix Factorication Model'
    def __init__(self):
        Thread.__init__(self)
        print('running Matrix Factorization')
        global cwd
        self.Name = 'Matrix Factorization Model'
        self.p = np.loadtxt("\\".join([cwd,"beers_p.csv"]),delimiter=',')
        self.q = np.loadtxt("\\".join([cwd,"beers_q.csv"]),delimiter=',')

        
    def setvars(self, dataMat, user, beer_list, user_id, review_idx, N=3):
        self.dataMat = dataMat
        self.user = user.reshape((len(beer_list,)))
        self.beer_list = beer_list
        self.N = N
        self.user_id = int(user_id)
        self.reviewed_idx = review_idx
    
    def recommendation(self):
        fP = self.p[self.user_id,:]
        mf_list = np.dot(fP,self.q.T)
        self.sorted_list = list(enumerate(mf_list))
        self.sorted_list = [beer for beer in self.sorted_list if beer[0] not in self.reviewed_idx]
        self.final_list = sorted(self.sorted_list, key=lambda x: x[1], reverse=True)

if __name__ == '__main__':
    MyApp().run()