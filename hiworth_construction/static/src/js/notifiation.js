//Desktop notification permission setting
$(document).ready(function(){
    if (Notification.permission !== "granted"){
        Notification.requestPermission();
    }
});