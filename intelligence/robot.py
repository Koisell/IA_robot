import math
import time

from cartographie.cercle import Cercle
from cartographie.ligne import Ligne
from boards.movingBase import MovingBase


class Robot:

    def __init__(self,nom,largeur):
        self.movingBase = None
        self.controlPanel = None
        self.collisionDetector = None
        self.nom = nom
        self.fenetre = None
        self.largeur = largeur
        self.chercher = None
        self.listPointInteret = None
        self.listVariables = []
        self.listPosition = []
        self.listTelemetre = []
        self.listBoard = []
        self.couleur=""
        self.countTest=0
        self.isSimulated = False
        self.x = 0
        self.y = 0
        self.angle = 0
        self.speed = 0
        self.movingDA = False
        self.movingDALastDist = 0
        self.movingDALastAngle = 0
        self.movingXY = False
        self.startTime = time.time()

    def __del__(self):
        self.closeConnections()

    def initialiser(self, chercher, listPointInteret, fenetre=None, simulate=False):
        self.isSimulated = simulate
        self.fenetre = fenetre
        self.chercher = chercher
        self.listPointInteret = listPointInteret
        if not self.isSimulated:
            for board in self.listBoard:
                if not board.connect():
                    print("ERROR: Unable to connect " + board.nom)
                    self.isSimulated = True
            for board in self.listBoard:
                if board.fonction == "movingBase":
                    self.movingBase = board
                elif board.fonction == "controlPanel":
                    self.controlPanel = board
                elif board.fonction == "collisionDetector":
                    self.collisionDetector = board
        if not self.controlPanel and any(board.fonction == "controlPanel" for board in self.listBoard):
            print("ERROR: No controlPanel found")
            self.isSimulated = True
        if not self.movingBase and any(board.fonction == "movingBase" for board in self.listBoard):
            print("ERROR: No movingBase found")
            self.isSimulated = True
        if not self.collisionDetector and any(board.fonction == "collisionDetector" for board in self.listBoard):
            print("ERROR: No collisionDetector found")
            self.isSimulated = True

        if(simulate != self.isSimulated):
            if(self.controlPanel):
                self.controlPanel.displayMessage("ERROR: Boards not found.")
                time.sleep(0.2)
                self.controlPanel.displayMessage("Stopping robot...")
            print "HALT: Stopping"
            exit(0)
        if self.isSimulated:
            self.movingBase = MovingBase("dummyBase","movingBase","")
            self.movingBase._isXYSupported = True
        return self.isSimulated

    def closeConnections(self):
        for board in self.listBoard:
            if board:
                board.disconnect()

    def dessiner(self):
        from cartographie.cercle import Cercle
        circle = Cercle(self.nom, self.x, self.y, self.largeur, "white")
        circle.dessiner(self.fenetre)
        line = Ligne("", self.x, self.y, self.x + self.largeur, self.y, "blue")
        line.rotate(self.angle)
        line.dessiner(self.fenetre)
        for telemetre in self.listTelemetre:
            line = Ligne("", self.x, self.y, self.x - telemetre.x, self.y + telemetre.y, "green")
            line.rotate(line.getAngle()+self.angle-90)
            line.dessiner(self.fenetre)
            circle = Cercle("", line.x2, line.y2, 10, "green")
            circle.dessiner(self.fenetre)
            lineTarget = Ligne("", line.x2, line.y2, line.x2*2, line.y2*2, "orange")
            lineTarget.resize(75);
            lineTarget.rotate(self.angle+telemetre.angle)
            lineTarget.dessiner(self.fenetre)

    def attendreDepart(self):
        if self.isSimulated:
            self.startTime = time.time()
            defaultValues = self.listPosition[1]
            if self.couleur != "":
                if self.couleur == self.listPosition[0].couleur:
                    defaultValues = self.listPosition[0]
                elif self.couleur == self.listPosition[1].couleur:
                    defaultValues = self.listPosition[1]
            self.couleur = defaultValues.couleur
            self.x = defaultValues.x
            self.y = defaultValues.y
            self.angle = defaultValues.angle #0 degres =3 heures
            if self.fenetre != None:
                self.dessiner()
            print("Le robot virtuel est " + self.couleur + " a la position x:" + str(self.x) + " y:" + str(self.y) + " angle:" + str(self.angle))
            return True
        else:
            oldColor=None
            self.displayScore(0)
            while (self.controlPanel.getStartSignal()):
                time.sleep(0.2)
            while(not self.controlPanel.getStartSignal()):
                self.startTime = time.time()
                color = self.controlPanel.getColor() #get the color
                if color != oldColor:
                    self.couleur = self.listPosition[color].couleur
                    self.x = self.listPosition[color].x
                    self.y = self.listPosition[color].y
                    self.angle = self.listPosition[color].angle #0=3h 180=9h
                    if self.movingBase and self.movingBase.isXYSupported():
                        self.movingBase.setPosition(self.x, self.y, self.angle)
                    print("Le robot est " + self.couleur)
                    self.controlPanel.displayMessage("Color: " + self.couleur)
                    oldColor = color
                time.sleep(0.2)

            #Set the initial positions
            print("Le robot est " + self.couleur + " a la position x:" + str(self.x) + " y:" + str(self.y) + " angle:" + str(self.angle))
            self.startTime = time.time()
            self.controlPanel.displayMessage("Start")
            self.movingBase.enableMovements() #authorize the robot to move
            return True

    def getRunningTime(self):
        return time.time() - self.startTime

    def attendreMilliseconde(self,duree):
        time.sleep(float(duree)/1000.0)
        return True

    def getVariable(self, nom):
        for variable in self.listVariables:
            if variable.nom == nom:
                return variable
        return None

    def displayScore(self, score):
        if(self.controlPanel):
            self.controlPanel.setScore(score)
        print("Score= "+str(score))

    def telemetreDetectCollision(self, speed=None):
        if self.isSimulated:
            return False
        if speed is None:
            speed = self.speed
        self.collisionDetector.updateTelemetre(self.listTelemetre)
        for telemetre in self.listTelemetre:
            if not telemetre.isValid():
                continue
            if speed < 0:
                if -80 < telemetre.angle < 80:
                    continue
            elif not -80 < telemetre.angle < 80:
                continue
            #print telemetre.nom, telemetre.value
            line = Ligne("", self.x, self.y, self.x - telemetre.x, self.y + telemetre.y, "green")
            line.rotate(line.getAngle()+self.angle-90)
            lineTarget = Ligne("", line.x2, line.y2, line.x2*2, line.y2*2, "purple")
            lineTarget.resize(telemetre.value*1.25)
            #extending the line by 1.25 makes more sure it detects colliding objects (not reported as unknown object)
            lineTarget.rotate(self.angle+telemetre.angle)
            if not 0 < lineTarget.x2 < self.chercher.largeur or not 0 < lineTarget.y2 < self.chercher.longueur:
                continue # Rejecting detections out of the map
            #lineTarget.dessiner(self.fenetre)
            if 5 < telemetre.value < 500:
                #Only test telemeter if the reported value is bellow 500mm
                containingElements = self.chercher.pointContenuListe(lineTarget.x1, lineTarget.y1, self.listPointInteret)
                listPointDetection = list(self.listPointInteret)
                for point in containingElements:
                    listPointDetection.remove(point)
                collision = self.chercher.enCollisionCarte(lineTarget, listPointDetection, True)
                if not collision:
                    #circle = Cercle(telemetre.nom, line.x2, line.y2, 20, "purple")
                    #circle.dessiner(self.fenetre)
                    #lineTarget.dessiner(self.fenetre)
                    print("/!\\"+telemetre.nom+" detected Unkown object. Position "+str(lineTarget.x2)+","+str(lineTarget.y2)+", angle "+str(lineTarget.getAngle())+ " at distance "+str(telemetre.value))
                    return [lineTarget.x2, lineTarget.y2]
                else:
                    print(telemetre.nom + " detected " + collision.nom)
        return False

    def executer(self,action):
        tabParam=[]
        for param in action.tabParametres:
            tabParam.append(param.getValue())
        if hasattr(self,action.methode):
            return getattr(self,action.methode)(*tabParam) #Run the requested method
        else:
            print "ERREUR: La methode",action.methode,"n'existe pas!!!"
            return False

    def positionAtteinte(self, x, y, angle, x1, y1, angle1, erreurPos, erreurAngle):
        if( (abs(x-x1) <= erreurPos) and (abs(y-y1) <= erreurPos) and (abs(angle-angle1) <= erreurAngle)):
            return True
        return False

    def distanceAtteinte(self,dist1, angle1, dist2, angle2 , erreurDist, erreurAngle):
        if( (abs(dist1-dist2) <= erreurDist) and (abs(angle1-angle2) <= erreurAngle) ):
            return True
        return False

    def getAngleToDo(self,angle):
        res = angle - self.angle
        if res > 180:
            res = -360 + res
        if res < -180:
            res = 360 + res
        return res

    def seDeplacerXY(self, x, y, absoluteAngle, vitesse=1.0):
        print "\t \t Deplacement: x:", x, " y:", y, " angle:", absoluteAngle
        self.updatePosition()
        chemin = self.chercher.trouverChemin(self.x,self.y,x,y,self.listPointInteret)
        if chemin == None:
            print "\t \t Chemin non trouve"
            return False
        for ligne in chemin:
            result = False
            if not self.movingBase.isXYSupported:
                result = self.seDeplacerDistanceAngle(ligne.getlongeur(), self.getAngleToDo(ligne.getAngle()))
                if not self.seDeplacerDistanceAngle(0, self.getAngleToDo(absoluteAngle), vitesse):
                    return False
            else:
                dirLine = Ligne("", self.x, self.y, x, y, "purple")
                direction = 1
                if abs(dirLine.getAngle() - self.angle) > 90:
                    direction = -1
                #print "Direction", direction
                if not self.telemetreDetectCollision(direction):
                    if not self.isSimulated:
                        self.movingBase.startMovementXY(x, y, absoluteAngle, vitesse)
                        result = self.__waitForMovementFinished(True)
                    else:
                        if self.fenetre:
                            dirLine.dessiner(self.fenetre)
                        self.x = x
                        self.y = y
                        self.angle = absoluteAngle
                        result = True
                else:
                    result = False
            if not result:
                return False
        if not self.isSimulated:
            return self.positionAtteinte(x, y, absoluteAngle, self.x, self.y, self.angle, 50, 5)
        else:
            return True

    def seDeplacerDistanceAngle(self,distance,angle,vitesse=1.0, retry=1):
        print "\t \tDeplacement: distance:", str(distance), " angle:", str(angle)

        if self.movingBase.isXYSupported:
            lineTarget = Ligne("", self.x, self.y, self.x*2, self.y*2, "purple")
            lineTarget.resize(distance)
            lineTarget.rotate(self.angle + angle)
            return self.seDeplacerXY(lineTarget.x2, lineTarget.y2,self.angle + angle, vitesse)
        if distance == 0 or not self.telemetreDetectCollision(distance):
            if not self.isSimulated:
                self.movingBase.startMovementDistanceAngle(distance, angle, vitesse)
                direction = 1
                if distance < 0:
                    direction = -1
                self.speed = vitesse*direction
                self.movingDA = True
                self.movingDALastDist = 0
                self.movingDALastAngle = 0
                result = self.__waitForMovementFinished(False, distance==0)
                self.movingDA = False
                return result
            else:
                self.updatePositionRelative(distance, angle)
                return True
        else:
            return False

    def __waitForMovementFinished(self, xyMove, rotationOnly=False, doNotAvoid=False):
        errorObstacle = False
        errorStuck = False
        time.sleep(0.1)  #wait 100ms before getting information on the movment
        print "waiting"
        status = self.movingBase.getMovementStatus()
        print status
        while "running" in status:
            self.updatePosition()
            status = self.movingBase.getMovementStatus()
            if not rotationOnly:
                collision = self.telemetreDetectCollision()
                if type(collision) != bool:
                    collisionX, collisionY = collision
                    print "Obstacle, stopping robot"
                    self.movingBase.emergencyBreak()
                    errorObstacle = True
                    break
        if "stuck" in status:
            errorStuck = True
            print "Stuck, stopping movement"
            self.movingBase.emergencyBreak()
        if xyMove:
            newX, newY, newAngle, speed = self.movingBase.getPositionXY()
            self.x = newX
            self.y = newY
            self.angle = newAngle
        else:
            distanceDone, angleDone, currentSpeed = self.movingBase.getPositionDistanceAngle()
            self.updatePositionRelative(distanceDone, angleDone)

        if errorObstacle or errorStuck:
            if not doNotAvoid:
                #self.eviterObstacle(self.angle, direction)
                pass
            return False
        return True

    def eviterObstacle(self, absoluteObstacleAngle, direction=1):
        print("\t \tEscape from A="+str(absoluteObstacleAngle))
        #Get opposed angle
        if absoluteObstacleAngle > 0:
            newAngle = absoluteObstacleAngle-180
        else:
            newAngle = absoluteObstacleAngle+180
        #newAngle = absoluteObstacleAngle
        xprev=self.x
        yprev=self.y
        newx = xprev + 300*math.cos(newAngle*0.0174532925) #rad
        newy = yprev + 300*math.sin(newAngle*0.0174532925) #rad
        ligne = Ligne("", xprev, yprev, newx, newy, "purple")
        distance = -1 * direction * ligne.getlongeur()
        #self.aveugler()
        time.sleep(0.2)
        self.seDeplacerDistanceAngle(distance, 0, 0.4, 0)
        time.sleep(0.2)
        #self.rendreVue()
        time.sleep(0.2)
        return True
        #search for a free opposed movment
        """escapePointInteretList = list(self.listPointInteret)
        escapeObstacles = self.chercher.pointContenuListe(xprev, yprev, escapePointInteretList)
        for elem in escapeObstacles:
            escapePointInteretList.remove(elem)
        for size in [400, 300, 250]:
            for a in range(0, 41, 10):
                for side in [-1, 1]:
                    lineTest = Ligne("", xprev, yprev, newx, newy, "purple")
                    lineTest.resize(size)
                    testAngle = lineTest.getAngle()+a*side
                    lineTest.rotate(lineTest.getAngle()+a*side)
                    if not self.chercher.enCollisionCarte(lineTest, escapePointInteretList):
                        print("\t \tFound collision escape")
                        print("\t \tEscape angle=" + str(lineTest.getAngle()))
                        distance = -1*direction*lineTest.getlongeur()
                        angleToDo = self.getAngleToDo(lineTest.getAngle())
                        if angleToDo>0:
                            angleToDo-=180
                        else:
                            angleToDo+=180
                        self.seDeplacerDistanceAngle(distance, angleToDo, 0.2, 0)
                        return True
                    elif (self.fenetre):
                        lineTest.dessiner(self.fenetre)
                        self.fenetre.win.redraw()"""
        return False

    def updatePositionRelative(self, distance, angle):
        angleDiff = (angle+self.angle)*0.0174532925  #rad
        xprev = self.x
        yprev = self.y
        self.x += distance*math.cos(angleDiff)
        self.y += distance*math.sin(angleDiff)
        self.angle += angle
        if self.angle > 180:
            self.angle = -360 + self.angle
        if self.angle < -180:
            self.angle = 360 + self.angle
        if self.fenetre != None:
            ligne = Ligne("",xprev,yprev,self.x,self.y,"green")
            ligne.dessiner(self.fenetre)
            self.fenetre.win.redraw()

    def updatePosition(self):
        if self.isSimulated:
            return
        if self.movingBase.isXYSupported:
            newX, newY, newAngle, speed = self.movingBase.getPositionXY()
            self.x = newX
            self.y = newY
            self.angle = newAngle
            self.speed = speed
        elif self.movingDA:
            distance, angle, speed = self.movingBase.getPositionDistanceAngle()
            self.speed = speed
            self.updatePositionRelative(distance-self.movingDALastDist, angle-self.movingDALastAngle)
            self.movingDALastDist = distance
            self.movingDALastAngle = angle
        else:
            self.speed = self.movingBase.getSpeed()

    def seDeplacerVersUnElement(self,type,vitesse=1,couleur=None):
        element = None
        if couleur==None:
            couleur = self.couleur
        #recherche de l'objet
        for obj in self.listPointInteret:
            if obj.type == type and (obj.couleur == couleur or obj.couleur not in [self.listPosition[0].couleur, self.listPosition[1].couleur]):
                element = obj
                break
        if element == None:
            print "\t \tElement non trouve!!!!" + type
            return False
        zoneAcces = element.zoneAcces
        if zoneAcces == None:
            print "\t \tL'element \""+element.nom+"\" n'a pas de zone d'acces"
            return False
        return self.seDeplacerXY(zoneAcces.x, zoneAcces.y, zoneAcces.angle, vitesse)


    def retirerElementCarte(self,type,couleur=None):
        element = None
        if couleur==None:
            couleur = self.couleur
        #recherche de l'objet
        for obj in self.listPointInteret:
            if obj.type == type and (obj.couleur == couleur or obj.couleur not in [self.listPosition[0].couleur, self.listPosition[1].couleur]):
                element = obj
                break
        if element == None:
            print "Element non trouve!!!!"
            return False
        self.chercher.updateNodesRemovingElement(element, self.listPointInteret)
        self.listPointInteret.remove(element)
        if self.fenetre:
            element.zoneEvitement.forme.couleur = "white"
            element.zoneEvitement.dessiner(self.fenetre)
            self.fenetre.win.redraw()
        return True

    def avancer(self,distance,vitesse=0.5):
        newx = self.x + distance * math.cos(self.angle * 0.0174532925)  # rad
        newy = self.y + distance * math.sin(self.angle * 0.0174532925)  # rad
        return self.seDeplacerXY(newx, newy, self.angle, vitesse)

    def reculer(self,distance,vitesse=0.5):
        newx = self.x + -distance * math.cos(self.angle * 0.0174532925)  # rad
        newy = self.y + -distance * math.sin(self.angle * 0.0174532925)  # rad
        return self.seDeplacerXY(newx, newy, self.angle, vitesse)

    def recaler(self, distance, axe, coordinate, angle, vitesse=0.2, coordinate2=None):
        success = True
        if not self.isSimulated:
            self.movingBase.startRepositioningMovement(distance, vitesse)
            direction = 1
            if distance < 0:
                direction = -1
            result = self.__waitForMovementFinished(False,direction,True)
            if result:
                print("ERROR: Movement wasn't stuck during the repositioning movement, the known angle should have a big error.")
                success = False
        if axe == "X":
            self.x = coordinate
        elif axe == "Y":
            self.y = coordinate
        elif axe == "XY":
            self.x = coordinate
            self.y = coordinate2
        self.angle = angle
        return success

    def incrementerVariable(self, variable):
        var = self.getVariable(variable)
        if var:
            var.incrementer()
        else:
            print("ERROR: Variable not found: " + str(variable))

    def decrementerVariable(self, variable):
        var = self.getVariable(variable)
        if var:
            var.decrementer()
        else:
            print("ERROR: Variable not found: " + str(variable))

    def resetVariable(self, variable):
        var = self.getVariable(variable)
        if var:
            var.set(0)
        else:
            print("ERROR: Variable not found: " + str(variable))
