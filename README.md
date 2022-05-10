# OlympiaRobotics (Colin was here)
This repository contains the code and documentation needed for the develoment of RoboFlagger.

<strong>Summary</strong>

RoboFlagger is a two robot system that can be operated manually or autonomously.
The three main software pieces required to run RoboFlagger are:
<ul>
  <li>client.py which should be ran on the raspberry pi. This processes commands issued by the controller (gui.py)</li>
  <li>gui.py which acts as the master controller for the raspberry pis</li>
  <li>sketch_robot.ino which controls the peripherals that roboflagger is equipped with</li>
</ul>

<strong>Git Workflow</strong>

To start a new branch and work locally on your own machine:
  1. git checkout -b "name of your branch"
  2. make changes to the branch
  3. type git status to view the changes you made
  4. do git add or git rm to add or remove changes you want to commit
  5. git commit -m "something you want to comment"
  6. git push to upload your local branch to origin
      Sometimes, the command prompt will tell you to upload stream. Yes, you want to create a new stream so follow the instructions.
   
To merge into master from github
  1. Create a pull request
  2. Select the branch you want to merge
  3. Preferably have a reviewer review your changes before confirming the pull request
