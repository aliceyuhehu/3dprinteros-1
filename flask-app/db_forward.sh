POD=$(oc get pods | grep mongo | grep -oP "^\S+-\d+-\S+")
echo THIS
echo $POD
echo END
oc port-forward $POD 27018:27017