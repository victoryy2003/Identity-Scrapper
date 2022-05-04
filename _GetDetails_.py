import os
import sys
import json
import platform
import requests
import urllib3

from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from urllib.request import urlopen

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def ClearScreen() :
    try:
        if platform.uname().system in ("Linux", "Darwin"):
            os.system("clear")
        elif platform.uname().system == "Windows":
            os.system("cls")
    except:
        pass


class _PlacesOfBirth :
    
    def __init__(self) :
        pass
    
    def Response () :
        
        PlacesCodeList = []
        PlacesNameList = []
        
        Session = requests.Session()
        
        PlacesHTML = Session.get("https://sapsnkra.moe.gov.my/ibubapa2/indexv2.php", verify = False)
        
        Locater = BeautifulSoup(PlacesHTML.text, "lxml")
        
        for Options in Locater.find_all("option") :
            
            if Options["value"] != "" :
                PlacesCodeList.append(Options["value"])
            if Options.text not in ("-PILIH NEGERI-", "-PILIH DAERAH-", "-PILIH SEKOLAH-") :
                PlacesNameList.append(Options.text)
        
        return (PlacesCodeList, PlacesNameList)

    def ResponseFromGivenAreaCode(UserInputAreaCode) :
        Data = _Get.RetrieveData()
        
        for PlaceCode in Data :
            for AreaCode in Data[PlaceCode] :
                if UserInputAreaCode == AreaCode :
                    return PlaceCode
                
        return None
    
    def ResponseFromGivenSchoolCode(UserInputSchoolCode) :
        Data = _Get.RetrieveData()
        
        for PlaceCode in Data :
            for AreaCode in Data[PlaceCode] :
                for SchoolCode in Data[PlaceCode][AreaCode] :
                    if UserInputSchoolCode == SchoolCode :
                        return PlaceCode
                    
        return None


class _Areas :
    
    def __init__(self, PlaceOfBirth) :
        self.PlaceOfBirth = PlaceOfBirth
    
    def Response (self) :
        
        AreasCodeList = []
        AreasNameList = []
        
        Session = requests.Session()
        
        AreasHTML = Session.get( f"https://sapsnkra.moe.gov.my/ajax/senarai_ppd.php?kodnegeri={self.PlaceOfBirth}", verify = False)
        
        Locater = BeautifulSoup(AreasHTML.text, "lxml")
        
        for Options in Locater.find_all("option"):
            
            if Options["value"] != "" :
                AreasCodeList.append(Options["value"])
            if Options.text not in ("-PILIH PPD-") :
                AreasNameList.append(Options.text)
        
        return (AreasCodeList, AreasNameList)
    
    def ResponseFromGivenSchoolCode(UserInputSchoolCode) :
        Data = _Get.RetrieveData()
        
        for PlaceCode in Data :
            for AreaCode in Data[PlaceCode] :
                for SchoolCode in Data[PlaceCode][AreaCode] :
                    if UserInputSchoolCode == SchoolCode :
                        return AreaCode
                    
        return None

class _Schools :
    
    def __init__(self, PlaceOfBirthCode, AreaCode) :
        self.PlaceOfBirthCode = PlaceOfBirthCode
        self.AreaCode = AreaCode
        
    def Response (self) :
        
        SchoolsCodeList = []
        SchoolsNameList = []
        Session = requests.Session()
        
        school_html = Session.get( f"https://sapsnkra.moe.gov.my/ajax/ddl_senarai_sekolah.php?kodnegeri={self.PlaceOfBirthCode}&kodppd={self.AreaCode}", verify = False)
        
        Locater = BeautifulSoup(school_html.text, "lxml")
        
        for Options in Locater.find_all("option"):
            
            if Options["value"] != "" :
                SchoolsCodeList.append(Options["value"])
            if Options.text not in ("-PILIH SEKOLAH-") :
                SchoolsNameList.append(Options.text)
        
        return (SchoolsCodeList, SchoolsNameList)


class _Get :
    
    def __init__(self, SchoolCode = None) :
        self.SchoolCode = SchoolCode
        
        if self.SchoolCode != None :
            PlaceOfBirthCode = _PlacesOfBirth.ResponseFromGivenSchoolCode(self.SchoolCode)
            AreaCode = _Areas.ResponseFromGivenSchoolCode(self.SchoolCode)
            
            if PlaceOfBirthCode != None and AreaCode != None :
                self.SchoolsList = _Schools(PlaceOfBirthCode, AreaCode).Response()
            else :
                raise Exception("PlaceOfBirthCode and AreaCode should not be None")
        
    def Response (self, BirthDate, PlaceOfBirth, FourDigitsNumber) :
        while True :
            try :
                Session = requests.Session()
                
                if FourDigitsNumber != None : # Run if Four Digits Number has been generated
                    
                    if self.SchoolCode == None : # If user didn't provided School Code
                        Response = Session.get( f"https://sapsnkra.moe.gov.my/ajax/papar_carian.php?nokp={BirthDate}{PlaceOfBirth}{FourDigitsNumber}", verify = False)
                        
                        if ("Tidak Wujud" not in Response.text) : 
                            return str ( f"{BirthDate}{PlaceOfBirth}{FourDigitsNumber}")
                            
                        elif ("Tidak Wujud" in Response.text) :
                            return str ( f"{BirthDate}{PlaceOfBirth}{FourDigitsNumber}\tNot Existing")
                    
                    
                    elif self.SchoolCode != None : # If user provided School Code
                        Response = Session.get( f"https://sapsnkra.moe.gov.my/ajax/papar_carianpelajar.php?nokp={BirthDate}{PlaceOfBirth}{FourDigitsNumber}&kodsek={self.SchoolCode}", verify = False)
                        
                        if ("Tidak Wujud" not in Response.text) : 
                            
                            SchoolsNameHTML = Session.get("https://sapsnkra.moe.gov.my/ibubapa2/semak.php", verify = False)
                            
                            Locater = BeautifulSoup(SchoolsNameHTML.text, "lxml")
                            StudentName = ((Locater.find(lambda t: t.text.strip() == "NAMA MURID")).find_next("td")).find_next("td")
                            
                            return str ( f"{BirthDate}{PlaceOfBirth}{FourDigitsNumber}\t{self.SchoolCode}\t{self.SchoolsList[1][self.SchoolsList[0].index(self.SchoolCode)]}\t{StudentName.text}")
                            
                        elif ("Tidak Wujud" in Response.text) :
                            return str ( f"{BirthDate}{PlaceOfBirth}{FourDigitsNumber}\t{self.SchoolCode}\t{self.SchoolsList[1][self.SchoolsList[0].index(self.SchoolCode)]}\tNot Existing")
                        
                return None
            except :
                continue
    
    def FourDigitsNumber(i, Gender) :
        if Gender in ("MALE", "FEMALE") :
            if Gender == "MALE" :
                if i%2 != 0 or i == 0 :
                    return f'{i:04}'
        
            elif Gender == "FEMALE" :
                if i%2 == 0 or i == 0 :
                    return f'{i:04}'
                
            return None
                
        else :
            return f'{i:04}'
        
    def RetrieveData() :
        
        try :
            open("Database.json", "r", encoding = "utf-8")
        except :
            open("Database.json", "w+", encoding = "utf-8")
            
        if ( datetime.utcfromtimestamp(os.path.getmtime("Database.json")) >= datetime.utcnow() - timedelta(days = 1) ) : # If last file modified time not more than 1 day
            if os.stat("Database.json").st_size != 0 : # If the file is not empty
                with open("Database.json", "r", encoding = "utf-8") as f :
                    return json.load(f)
            
        Data = {}
        Places = _PlacesOfBirth.Response()
            
        for PlaceCode in Places[0] :
            Data[PlaceCode] = {}
            Areas = _Areas(PlaceCode).Response()
            
            for AreaCode in Areas[0] :
                Data[PlaceCode][AreaCode] = []
                Schools = _Schools(PlaceCode, AreaCode).Response()
                
                for SchoolCode in Schools[0] :
                    Data[PlaceCode][AreaCode].append(SchoolCode)
        
        with open ("Database.json", "w", encoding = "utf-8") as f :
            json.dump(Data, f, indent = 4, ensure_ascii = False, sort_keys = True)

        return Data
    
    def VerifyCode(Code) :
        Data = _Get.RetrieveData()
        
        for PlaceCode in Data :
            if Code == PlaceCode :
                return True
            
            for AreaCode in Data[PlaceCode] :
                if Code == AreaCode :
                    return True
                
                for SchoolCode in Data[PlaceCode][AreaCode] :
                    if Code == SchoolCode :
                        return True

        return False


if __name__ == "__main__" : # A program to get All the Code Listing including Places of Birth Code, Area Code, School Code that available
    
    _Get.RetrieveData()
    
    while True :
        
        ClearScreen()
        Places = _PlacesOfBirth.Response()
        for PlacesName in Places[1] :
            print (PlacesName)
            
        print( "-"*20)
        UserInputPlaceCode = str (input("Please enter the place of birth : (13) "))
        ClearScreen()
        
        if UserInputPlaceCode in Places[0] :
            
            
            Areas = _Areas(UserInputPlaceCode).Response()
            for AreasName in Areas[1] :
                print (AreasName)
                
            print( "-"*20)
            print( f"Place of Birth : {Places[1][Places[0].index(UserInputPlaceCode)]}")
            print( "-"*20)
            UserInputAreaCode = str (input("Please enter the area code : (Y040) "))
            ClearScreen()
            
            if UserInputAreaCode in Areas[0] :
                
                Schools = _Schools(UserInputPlaceCode, UserInputAreaCode).Response()
                for i in range(len(Schools[0])) :
                    print ( f"{Schools[0][i]}\t   {Schools[1][i]}")
                
                print( "-"*20)
                print( f"Place of Birth : {Places[1][Places[0].index(UserInputPlaceCode)]}")
                print( f"Area : {Areas[1][Areas[0].index(UserInputAreaCode)]}")
                print( "-"*20)
                UserInputSchoolCode = str (input("Please enter the school code : (YCC4102) "))
                ClearScreen()
                
                if UserInputSchoolCode in Schools[0] :
                    print( "-"*20)
                    print( f"Place of Birth Code : {UserInputPlaceCode}")
                    print( f"Area Code : {UserInputAreaCode}")
                    print( f"School Code : {UserInputSchoolCode}")
                    print( "-"*20)
                    print( "And that's all you need, you might use these information")
                    print( "on the __main__.py script, or you may re-run this script")
                    print( "to get more information\n")
                
                    break
            
        input ( "You had entered wrong code, please try again\nPress enter to continue...")
