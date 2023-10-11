export(copyto clipboard, paste in terminal) AWS credentials from AWS acc page (comm line access, option 1)
 - will give access key, secret access key and session token

to deploy lambda in AWS:
in terminal type (vs code, make sure you're in the right directory first):
 -comment : if __name__ == "__main__": etc. (working locally this should be uncommeted)
 - run: ./deploy-lambda.sh

 To run in local:
 do same export step as above
 uncomment __main__ 
 in vs terminal run: python handler.py

(make sure all files have been saved)
 profit!