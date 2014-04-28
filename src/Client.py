import Connessione
import random
import socket
import string
import Util
import SharedFile
import SharedFileService
import SearchResult
import SearchResultService


from signal import signal, SIGPIPE, SIG_DFL
signal(SIGPIPE,SIG_DFL)

class Client:
    
    @staticmethod
    def visualizza_menu_principale():
        
        while True:
            if(Util.USEMODE=="PEER"):
                print("\n************************\n*  1 - Ricerca File    *\n*  2 - Login           *\n*  3 - Carica File     *\n*  4 - Download File   *\n*  5 - Rimuovi File    *\n*  6 - Logout          *\n*  0 - Fine            *\n************************")
            else:
                print("\n************************\n*  1 - Ricerca File    *\n*  2 - Carica File     *\n*  3 - Download File   *\n*  4 - Rimuovi File    *\n*  0 - Fine            *\n************************")
            out=raw_input("\n\tOperazione scelta: ")
            if(Util.USEMODE=="PEER" and (int(out) >= 0 and int(out) <= 6 ) or Util.USEMODE=="SUPERPEER" and(int(out) >= 0 and int(out) <= 4) ):
                break
            print("Valore inserito errato!")
        
        return out
    
    
    @staticmethod
    def login(SessionID):
        stringa_da_trasmettere="LOGI"+Util.HOST+Util.Util.adattaStringa(5,str(Util.PORT) )
        try:
            sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            sock.connect((Util.IPSuperPeer, int(Util.PORTSuperPeer) ))
            sock.send(stringa_da_trasmettere.encode())
            risposta=sock.recv(21)
            print(risposta)
            nuovosessionid=risposta[4:20]
            sock.close()
        except Exception as e:
            print e
            print "Errore login"
        if(nuovosessionid=="0000000000000000"):
            return SessionID
        else:
            return nuovosessionid
            
    @staticmethod
    def logout(SessionID):
        print(SessionID+"nel logout")
        if(SessionID != "" and SessionID != "0000000000000000"):
            stringa_da_trasmettere="LOGO"+SessionID
            print("str da trasmeteer"+stringa_da_trasmettere)
            try:
                sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
                sock.connect((Util.IPSuperPeer, int(Util.PORTSuperPeer) ))
                sock.send(stringa_da_trasmettere.encode())
                risposta=sock.recv(7)
                print(risposta)
                print "File eliminati dal supernpeer: "+str(risposta[4:7])
                sock.close()
            except Exception as e:
                print e
                print "Errore logout"
        return ""
    
    
    @staticmethod
    def addFile(SessionID):
        nomefile=""
        filemad5=""
        
        #aggiungo file nella tabella del peer SharedFile
        try:
            conn_db = Connessione.Connessione()
            nomefile = raw_input("Inserire il nome del file: " + Util.LOCAL_PATH)
            filemd5 = Util.Util.get_md5(Util.LOCAL_PATH + nomefile)
            print("md5: " + filemd5+"lunghezza: "+str(len(filemd5))+ "nome: " + nomefile)
            file = SharedFileService.SharedFileService.insertNewSharedFile(conn_db.crea_cursore(), filemd5, nomefile)
            
        except Exception as e:
            print e
            print("Errore aggiunta file")
        
        finally:
            conn_db.esegui_commit()
            conn_db.chiudi_connessione()
        
        #formatto e invio stringa di aggiunta file nel superpeer    
        try:
            #nomefile = Util.Util.aggiungi_spazi_finali(nomefile,100)
            stringa_da_inviare="ADFF"+SessionID+filemd5+nomefile
            print(stringa_da_inviare)
            sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            sock.connect((Util.IPSuperPeer, int(Util.PORTSuperPeer) ))
            sock.send(stringa_da_inviare)
            sock.close()
        except Exception as e:
            print e
            print("Errore per contattare il superpeer in add file")
        
    @staticmethod
    def deleteFile(SessionID):
        
        ricerca=""
        sharedfile=[]
        choice=0
        try:
            ricerca=raw_input("Inserire stringa di ricerca del file: ")
            conn_db = Connessione.Connessione()
            sharedfile=SharedFileService.SharedFileService.getSharedFiles(conn_db.crea_cursore(),ricerca)
            i = 0
            while i < len(sharedfile):
                print("\t"+str(i + 1) + ".\t" + sharedfile[i].filename)
                i = i + 1
        
            #il valore di choice e' incrementato di uno
            choice = int(raw_input("\t  Scegliere il numero del file da cancellare (0 annulla): ")) 
            if(choice>0):
                sharedfile[choice-1].delete(conn_db.crea_cursore())
                print("File eliminato")
            
        except Exception as e:
            print e
            print"Errore nell'eliminazione del file da database locale"
        
        finally:
            conn_db.esegui_commit()
            conn_db.chiudi_connessione()
            
        try:
            if(choice>0):
                stringa_da_inviare="DEFF"+SessionID+sharedfile[choice-1].filemd5
                sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
                sock.connect((Util.IPSuperPeer, int(Util.PORTSuperPeer) ))
                sock.send(stringa_da_inviare)
                sock.close()
            
        except Exception as e:
            print e
            print"Errore nel contattare il superpeer nell'eliminazione del file"
            
    @staticmethod 
    def searchHandler(SessionID):
        while True:
            query_ricerca = raw_input("\n\tInserire la stringa di ricerca (massimo 20 caratteri): ")
            if(len(query_ricerca) <= 20):
                break
            print("\n\tErrore lunghezza query maggiore di 20!")
        query_ricerca = Util.Util.riempi_stringa(query_ricerca, 20)
        stringa_da_trasmettere="FIND"+SessionID+query_ricerca
        print "Invio supernodo: "+stringa_da_trasmettere
        
        try:
            sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            sock.connect((Util.IPSuperPeer, int(Util.PORTSuperPeer)) )
            sock.send(stringa_da_trasmettere.encode())
            sock.close()
            
        except Exception as e:
            print e
            print"Errore nel contattare il supernodo per ricerca file"
            

    @staticmethod
    def downloadFile():
        
        conn_db = Connessione.Connessione()
        searchResults = SearchResultService.SearchResultService.getSearchResults(conn_db.crea_cursore())
        conn_db.esegui_commit()
        conn_db.chiudi_connessione()
        
        i = 0
        while i < len(searchResults):
            print("\t"+str(i + 1) + ".\t" + searchResults[i].filename + "\t"+searchResults[i].ipp2p + "\t" + searchResults[i].pp2p)
            i = i + 1
        
        #il valore di choice e' incrementato di uno
        choice = int(raw_input("\t  Scegliere il numero del peer da cui scaricare (0 annulla): ")) 
        if(choice > 0):
            sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)        
            sock.connect((searchResults[choice - 1].ipp2p, int(searchResults[choice - 1].pp2p)))
            sendingString = "RETR" + searchResults[choice - 1].filemd5
            #sock.send(sendingString.encode())
            sock.send(sendingString)

            receivedString = sock.recv(10)        
            if receivedString[0:4].decode() == "ARET":
                nChunk = int(receivedString[4:10].decode())            
                chunk = bytes()
                chunkCounter = 0

                file = open(Util.LOCAL_PATH + searchResults[choice - 1].filename, "wb")
                
                #inizializzo la variabile temporanea per stampre la percentuale
                tmp = -1
                print "\nDownloading...\t",
                
                while chunkCounter < nChunk:
                    receivedString = sock.recv(1024)
                    chunk = chunk + receivedString                

                    while True:
                        
                        #Un po' di piacere per gli occhi...
                        perCent = chunkCounter*100//nChunk
                        if(perCent % 10 == 0 and tmp != perCent):
                            if(tmp != -1):
                                print " - ",
                            print str(perCent) + "%",
                            tmp = perCent
                        
                        if len(chunk[:5]) >=  5:
                            chunkLength = int(chunk[:5])
                        else:
                            break

                        if len(chunk[5:]) >= chunkLength:
                            data = chunk[5:5 + chunkLength]
                            file.write(data)
                            chunkCounter = chunkCounter + 1
                            chunk = chunk[5 + chunkLength:]
                        else:
                            break

                file.close()
                print ""

            sock.close() 

            #controllo correttezza del download
            myMd5 = Util.Util.md5(Util.LOCAL_PATH + searchResults[choice - 1].filename)        
            if myMd5 != searchResults[choice - 1].filemd5:
                print("Errore nel download del file, gli md5 sono diversi!")  
        else:
            print("Annullato")