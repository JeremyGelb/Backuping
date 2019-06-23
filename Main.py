# -*- coding: utf-8 -*-
"""
Created on Sun May 12 16:44:08 2019

@author: gelbj
"""

import os
import shutil
import sys
import time
from datetime import datetime
from distutils.dir_util import copy_tree
from multiprocessing.dummy import Pool as ThreadPool 

from PathLib import Path



#########################################
##Fonction utilitaires
#########################################

AsZippedFolder = [".Data",".gdb",".git"]
PassThisFiles = ["__pycache__",".git",".Trashes","DataSystem Volume Information","System Volume Information"]

def NiceDuration(Nb) : 
    Hours = int(Nb/3600)
    Mins = int((Nb-Hours*3600) / 60)
    Secs = int(Nb-Hours*3600-Mins*60)
    if len(str(Hours))==1 : 
        Hour = "0"+str(Hours)
    else : 
        Hour = str(Hours)
    if len(str(Mins))==1 : 
        Min = "0"+str(Mins)
    else : 
        Min = str(Mins)
    if len(str(Secs))==1 : 
        Sec = "0"+str(Secs)
    else : 
        Sec = str(Secs)
    return ":".join([Hour,Min,Sec])

def CheckLength(File) : 
    if len(File)>260 : 
        if "." in File.name :
            Elements = File.name.split(".")
            FileName = ".".join(Elements[0:-1])
            Ext = Elements[-1]
            Remain = 260-len(File.parent)-2-len(Ext)
            NewFile = File.parent.joinpath(FileName[0:Remain-1]+"."+Ext)
        else : 
            FileName = File.name
            Remain = 260-len(File.parent)-2
            NewFile = File.parent.joinpath(FileName[0:Remain-1])
        print("This file : "+File+" has a too long name he will be renamed as : "+FileName[0:Remain-1]+"."+Ext)
        return NewFile
    else : 
        return File

def FindName(File) : 
    Root = str(File.parent)
    Name = File.name
    i=1
    while os.path.isfile(File) :
       Nb = str(i)
       if len(Nb)==1 : 
           Nb = "0"+Nb
       if "." in Name : 
           Elements = Name.split(".")
           ActualName = Elements[0]+Nb+"."+".".join(Elements[1:len(Elements)])
       else : 
           ActualName = Name+Nb
       File = Path(Root+"/"+ActualName) 
       i+=1
    return File


def WalkFolders(Root) : 
    """
    Fonction permettant de lister des archives et des dossiers
    """
    Folders = []
    Zipped = []
    for root, dirs, files in os.walk(Root, topdown=False) : 
        root = Path(root)
        for FolderName in dirs :
            Folder = root.joinpath(FolderName)
            Inter2 = set(PassThisFiles).intersection(set(Folder.split("/")))
            if len(Inter2) == 0 : 
                AreIn = [Type in Folder for Type in AsZippedFolder]
                if not True in AreIn : 
                    Folders.append(Folder)
                else :
                    InName = [element in FolderName for element in AsZippedFolder]
                    InPath = [element in Folder.parent for element in AsZippedFolder]
                    if True in InName and True not in InPath :
                        Zipped.append(Folder)
    return Folders,Zipped


def WalkFiles(Root) : 
    Files = []
    for root, dirs, files in os.walk(Root, topdown=False) :
        root = Path(root)
        for FileName in files : 
            File = root.joinpath(FileName)
            AreIn = [Type in File for Type in AsZippedFolder]
            Inter2 = set(PassThisFiles).intersection(set(File.split("/")))
            if len(Inter2) == 0 and True not in AreIn : 
                Files.append(File)
    return Files
            
            
def PrepareOuput(OutPath) : 
    """
    cree des repertoires dans la sortie si besoin
    Data : la ou la copie a lieu
    OldVersion : garde des copies en ancienne version
    Deleted : corbeille temporaire
    """
    for Folder in ["Data","OldVersion","Deleted","logs"] : 
        if os.path.isdir(OutPath.joinpath(Folder)) == False : 
            os.mkdir(OutPath.joinpath(Folder))



def CompleteDirTree(Root1,Root2) : 
    """
    Permet de s'assurer que l'arborescence de 1 se retrouve bien dans 2
    et la complete au besoin
    Based on : https://stackoverflow.com/questions/40828450/how-to-copy-folder-structure-under-another-directory
    """
    Root1 = str(Root1).replace("\\","/")
    Root2 = str(Root2).replace("\\","/")
    for root, dirs, files in os.walk(Root1, topdown=False) : 
        for Folder in dirs :
            Folder = (root+"/"+Folder).replace("\\","/")
            Folder = Root2 +"/"+ Folder[len(Root1):len(Folder)]
            AreIn = [Type in Folder for Type in AsZippedFolder]
            Inter2 = set(PassThisFiles).intersection(set(Folder.split("/")))
            if len(Inter2)==0 and (not True in AreIn) : 
                os.makedirs(Folder,exist_ok=True)
            

            
def CleanOldVersion(OldPath,MaxTime) : 
    """
    permet de transferer les fichiers dans OldVersion qui devront
    basculer dans Deleted
    """
    Operations = []
    now = datetime.now()
    Dest = OldPath.parent.joinpath("Deleted")
    ##Verification des archives
    for Folder in OldPath.walkdirs() : 
        if Folder.name not in PassThisFiles :
            for element in AsZippedFolder : 
                if element in Folder.name : 
                    if abs(datetime.timestamp(now) - os.path.getctime(Folder)) > MaxTime :
                        # cas ou le fichier n'est pas present dans le dossier deleted
                        if os.path.isdir(Dest+"/"+Folder.name)==False and os.path.isfile(Dest+"/"+Folder.name)==False :
                            Operations.append([(shutil.copytree,(str(Folder),Dest+"/"+Folder.name),"Archive copied to  :  "+str(Dest+"/"+Folder.name)),
                                (shutil.rmtree,(Folder),"Old archive deleted : "+str(Folder))
                        ])
                        # sinon :
                        else : 
                            Operations.append([
                                (shutil.rmtree,(Dest.replace("\\","/")+"/"+Folder.name),"previous old archive deleted : "+str(Dest+"/"+Folder.name)),
                                (shutil.copytree,(str(Folder),Dest+"/"+Folder.name),"Archive copied to  :  "+str(Dest+"/"+Folder.name)),
                                (shutil.rmtree,(Folder),"Old archive deleted : "+str(Folder))
                        ])
                        
                    #copy_tree(str(Folder),Dest.joinpath(Folder.name))
    ##Verification des fichiers
    for File in OldPath.walkfiles() : 
        if abs(datetime.timestamp(now) - os.path.getmtime(File)) > MaxTime*24*60*60 : 
            #cas ou le fichier n'est pas present dans le dossier deleted
            if os.path.isfile(str(Dest+"/"+File.name))==False :
                Operations.append([
                    (shutil.move,(str(File),str(Dest+"/"+File.name)),"File moved to Deleted : "+str(File))
                    ])
            #sinon
            else : 
                Operations.append([
                    (os.remove,(str(Dest+"/"+File.name)),"previous old file deleted : "+str(Dest+"/"+File.name)),
                    (shutil.move,(str(File),str(Dest+"/"+File.name)),"File moved to Deleted : "+str(File))
                    ])
            
            #shutil.move(File,Dest.joinpath(File.name))
    return Operations
        
        
    
def CleanDeleted(DeletePath,MaxTime) : 
    """
    permet de supprimer definitivement les fichiers de Deleted quand
    leur date de perempsion est atteinte
    """
    Operations = []
    now = datetime.now()
    ##Verification des archives
    for Folder in DeletePath.walkdirs() : 
        if Folder.name not in PassThisFiles :
            for Element in AsZippedFolder : 
                if Element in Folder.name : 
                    if datetime.timestamp(now) - os.path.getctime(Folder) > MaxTime : 
                        #shutil.rmtree(Folder)
                        Operations.append([(shutil.rmtree,(Folder),"Archive deleted because too old : "+str(Folder))])
    ## Verification des fichiers
    for File in DeletePath.walkfiles() : 
        if datetime.timestamp(now) - os.path.getctime(File) > MaxTime*24*60*60 : 
            #os.remove(File)
            Operations.append([(os.remove,(File),"File deleted because too old : "+str(File))])
    return Operations
            
            
def ArchiveCopy(Folder,Root1,Root2) : 
    """
    Fonction permettant de copier un fichier archive dans la destination
    en verifiant sa derniere date de modification
    """
    Operations = []
    RelativePath = str(Folder)[len(str(Root1)):len(Folder)]
    OutPath = Path(Root2+"\\Data/"+RelativePath)
    OldVersionPath = Path(Root2+"\\OldVersion/"+RelativePath)
    #si le fichier n'existe pas, il faut le copier
    if OutPath.isdir()==False : 
        Operations.append([(shutil.copytree,(str(Folder),str(OutPath)),"Saving this new archive : "+Folder)])
        #copy_tree(str(Folder),str(OutPath))
    else : 
        #il faut verifier que celui existant ne colle pas en terme de date
        Date1 = os.path.getmtime(Folder)
        Date2 = os.path.getmtime(OutPath)
        if abs(Date1 - Date2) > 15 : #on tolere un ecart max de 15secondes
            #il faut deplacer l'ancien vers sa nouvelles maison
            Name = Folder.name.split(".")
            Date = datetime.utcfromtimestamp(int(Date1)).strftime("%d-%m-%Y")
            FinalName = Name[0]+"_"+Date+"."+Name[1]
            NewFolder = OldVersionPath.parent.joinpath(FinalName)
            NewName = FindName(NewFolder)
            Operations.append([
                    (shutil.copytree,(OutPath,NewName),"Backing the previous version : "+NewFolder),
                    (shutil.rmtree,(OutPath),"Replacing the olversion (deletion) : "+OutPath),
                    (shutil.copytree,(Folder,OutPath),"Replacing the olversion (copy) : "+OutPath)
                    ])
            #copy_tree(OutPath,NewFolder)
            #ensuite il faut supprimer l'ancien
            #shutil.rmtree(OutPath)
            #et finalement y mettre les nouveaux fichiers
            #copy_tree(Folder,OutPath)
    return Operations
            
            

def FileCopy(File,Root1,Root2) : 
    """
    Fonction permettant de copier un fichier dans la destination
    en verifiant sa derniere date de modification
    """
    Operations =[]
    RelativePath = str(File)[len(str(Root1)):len(File)]
    OutPath = Path(Root2+"/Data/"+RelativePath)
    OldVersionPath = Path(Root2+"/OldVersion/"+RelativePath)
    #si le fichier n'existe pas, il faut le copier
    if os.path.isfile(OutPath)==False : 
        Out =CheckLength(OutPath)
        Operations.append([(shutil.copy2,(str(File),Out),"Saving this new File : "+File)])
        #shutil.copy2(str(File),str(OutPath))
    else : 
        #il faut verifier que celui existant ne colle pas en terme de date
        Date1 = os.path.getmtime(File)
        Date2 = os.path.getmtime(OutPath)
        if abs(Date1 - Date2) > 15 : #on tolere un ecart max de 15 secondes
            #il faut deplacer l'ancien vers sa nouvelles maison
            Name = File.name.split(".")
            Date = datetime.utcfromtimestamp(int(Date1)).strftime("%d-%m-%Y")
            if len(Name)==1 : 
                FinalName = Name[0]+"_"+Date
            else :
                FinalName = Name[0]+"_"+Date+"."+".".join(Name[1:len(Name)])
            #NewFile = GetParent(OldVersionPath)+"/"+FinalName
            NewFile = CheckLength(OldVersionPath.parent.joinpath(FinalName))
            NewName = FindName(NewFile)
            Operations.append([
                    (shutil.copy2,(OutPath,NewName),"backing the previous version : "+NewFile),
                    (os.remove,(OutPath),"Replacing the olversion (deletion) : "+OutPath),
                    (shutil.copy2,(File,OutPath),"Replacing the olversion (copy) : "+OutPath)
                    ])
            #shutil.copy2(OutPath,NewFile)
            #ensuite il faut supprimer l'ancien
            #os.remove(OutPath)
            #et finalement y mettre les nouveaux fichiers
            #print("Saving the new version : "+OutPath)
            #shutil.copy2(File,OutPath)
    return Operations

            
def Execute(Operations,NbCores) : 
    """
    Permet d'executer en parallele les operations
    """
    pool = ThreadPool(NbCores)
    results = pool.map(Worker,Operations)
    return results


def Execute2(Operations,NbCores) : 
    """
    Permet d'executer en parallele les operations
    """
    pool = ThreadPool(NbCores)
    results = pool.map(Worker2,Operations)
    return results


def Worker(Operations) : 
    """
    Fonction qui connait son travail
    """
    Done = []
    for Operation in Operations :
        for Function,Params,Message in Operation : 
            if type(Params)!=tuple : 
                Function(Params)
            else :
                Function(*Params)
            Done.append(Message)
    return Done


def Worker2(Operations) : 
    """
    Fonction qui connait son travail
    """
    Done = []
    for Function,Params,Message in Operations : 
        if type(Params)!=tuple : 
            Function(Params)
        else :
            Function(*Params)
        Done.append(Message)
    return Done

def StartBackup(Root1,Root2,UpdateVersions = False, UpdateDelete=False, MaxTimeVersion = 30, MaxTimeDelete=30,NbCores=1) : 
    """
    Fonction principale permettant d'effectuer le backup
    """
    ## Etape1 : verifier si les dossiers de reception sont la
    PrepareOuput(Root2)
    DataPath = Root2.joinpath("/Data")
    OldPath = Root2.joinpath("/OldVersion")
    DeletedPath = Root2.joinpath("/Deleted")
    Now = datetime.now()
    LogPath = Root2.joinpath("/logs/logs_"+Now.strftime("%d-%m-%Y")+".txt")
    LogFile = FindName(LogPath)
    ## Etape2 : mettre a jour l'arborescence
    print("--------Preparing the folders---------")
    CompleteDirTree(Root1,DataPath)
    CompleteDirTree(Root1,OldPath)
    ## Etape4 : parcourir les dossier et copier les archives
    Copied = []
    Operations1 = []
    Folders,Zippeds = WalkFolders(Root1)
    for Zipped in Zippeds : 
        Folder = Path(Zipped)
        print(Folder)
        Operations1.append(ArchiveCopy(Folder,Root1,Root2))
        Copied.append(Folder.name)
        
#    #Execution des copie
    print("--------Executing the copy of archives---------")
    Messages1 = Execute(Operations1,NbCores)
    Archives = set(Copied)
#    
    ## Etape5 : parcourir les fichiers et les copiers
    Operations1 = []
    Files = WalkFiles(Root1)
    print("Number of files found : "+str(len(Files)))
    for File in Files  : 
        File = Path(File)
        Operations1.append(FileCopy(File,Root1,Root2))
      
    print("--------Executing the copy of the files---------")
    Messages2 = Execute(Operations1,NbCores)
    
    
    ## Etape6 : mettre a jour le dossier avec les anciennes versions
    if UpdateVersions : 
        print("--------Executing the update of old files---------")
        WaitTimeVersion = MaxTimeVersion*24*60*60
        Operations1 = CleanOldVersion(OldPath,WaitTimeVersion)
        Messages3 = Execute2(Operations1,NbCores)
    if UpdateDelete : 
        print("--------Executing the cleaning of deleted files---------")
        WaitTimeDelete = MaxTimeDelete*24*60*60
        Operations1 = CleanDeleted(DeletedPath,WaitTimeDelete)
        Messages4 = Execute2(Operations1,NbCores)
    
    print("--------writing the logs---------")
    AllMessages = Messages1 + Messages2 + Messages3 + Messages4
    Logs = open(LogFile,"w")
    for Messages in AllMessages : 
        for Message in Messages :
            try :
                Logs.write(Message+"\n")
            except UnicodeEncodeError : 
                pass
    Logs.close()
        
                
    

#########################################
##Execution
#########################################
        
Parameters = [
#        {"InputFolder" :"L:/",
#         "OutputFolder":"Z:/CLEFS/PyBackup/JG_DOC",
#         "CleanVersion":True,"CleanOld":True,"WaitVersion":30,"WaitDelete":30, "NbCores":40},
#        {"InputFolder" :"G:/",
#         "OutputFolder":"F:/CLEFS/PyBackup/JG_PROJ",
#         "CleanVersion":True,"CleanOld":True,"WaitVersion":30,"WaitDelete":30, "NbCores":40},
#        {"InputFolder" :"I:/",
#         "OutputFolder":"F:/__PyKeysBackup/JG_PROG",
#         "CleanVersion":True,"CleanOld":True,"WaitVersion":30,"WaitDelete":30, "NbCores":40},
        {"InputFolder" :"H:/",
         "OutputFolder":"F:/__PyKeysBackup/JG_DOC",
         "CleanVersion":True,"CleanOld":True,"WaitVersion":30,"WaitDelete":30, "NbCores":40},
#          {"InputFolder" :"J:/",
#         "OutputFolder":"Z:/CLEFS/PyBackup/JG_PROJ",
#         "CleanVersion":True,"CleanOld":True,"WaitVersion":30,"WaitDelete":30, "NbCores":40},
#        {"InputFolder" :"G:/",
#         "OutputFolder":"F:/__PyKeysBackup/JG_PROJ",
#         "CleanVersion":True,"CleanOld":True,"WaitVersion":30,"WaitDelete":30, "NbCores":40},
        #{"InputFolder" :"","OutputFolder":"","CleanVersion":True,"CleanOld":True,"WaitVersion":30,"WaitDelete":30},
        #{"InputFolder" :"","OutputFolder":"","CleanVersion":True,"CleanOld":True,"WaitVersion":30,"WaitDelete":30}
        
        
        ]

i=1
for Dico in Parameters :
    print("-------------------Staring the command number "+str(i))
    start_time = time.time()
    StartBackup(Path(Dico["InputFolder"]),Path(Dico["OutputFolder"]),UpdateVersions = Dico["CleanVersion"], UpdateDelete= Dico["CleanOld"], MaxTimeVersion = Dico["WaitVersion"], MaxTimeDelete=Dico["WaitDelete"],NbCores=Dico["NbCores"])
    elapsed_time = time.time() - start_time
    print("Time used to do all operations : "+NiceDuration(elapsed_time))
    i+=1
    print("")
    print("")