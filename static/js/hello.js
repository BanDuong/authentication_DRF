$(document).ready(function(){
    document.getElementById('h1').innerHTML = "Show information users!";
    $("#bt_show").on('click', function(){
        $.ajax({
           url: '/ajax/',
            method: 'GET',
            success: function(data){
               let d = data;
               alert(data);
            },
            fail: function(data){
                alert('Got an error dude');
            }
        });
        // alert('hiii');
    });
});
