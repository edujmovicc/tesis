/* global $ */

$(document).ready(load)
 var g_tabla_titulos, g_tabla_alumnos, g_tabla_tutores;
 var table_language = {
            "sProcessing":     "Procesando...",
            "sLengthMenu":     "Mostrar _MENU_ registros",
            "sZeroRecords":    "No se encontraron resultados",
            "sEmptyTable":     "Ningún dato disponible en esta tabla",
            "sInfo":           "Mostrando registros del _START_ al _END_ de un total de _TOTAL_ registros",
            "sInfoEmpty":      "Mostrando registros del 0 al 0 de un total de 0 registros",
            "sInfoFiltered":   "(filtrado de un total de _MAX_ registros)",
            "sInfoPostFix":    "",
            "sSearch":         "Buscar:",
            "sUrl":            "",
            "sInfoThousands":  ",",
            "sLoadingRecords": "Cargando...",
            "oPaginate": {
                "sFirst":    "Primero",
                "sLast":     "Último",
                "sNext":     "Siguiente",
                "sPrevious": "Anterior"
            },
            "oAria": {
                "sSortAscending":  ": Activar para ordenar la columna de manera ascendente",
                "sSortDescending": ": Activar para ordenar la columna de manera descendente"
            }
    };
function load(){
    g_tabla_titulos = $('#tabla_titulos').DataTable( {
        "order": [[ 0, "desc" ]],
        "language": table_language,
        "bFilter": false
    } );
    
    g_tabla_alumnos = $("#tabla_alumnos").DataTable( {
        "order": [[ 0, "desc" ]],
        "language": table_language,
        "bFilter": false
    } );
    
    g_tabla_tutores = $("#tabla_tutores").DataTable( {
        "order": [[ 0, "desc" ]],
        "language": table_language,
        "bFilter": false
    } );
}

function obtenerLineaYTutores(){
    var nuevo_titulo = $("#nuevo_titulo")[0].value;
    $.ajax({
        url: "/obtener_linea_y_tutores",
        type: "POST",
        data: JSON.stringify({"nuevo_titulo": nuevo_titulo}),
        contentType: "application/json",
        success: function(data){
            var result = JSON.parse(data);
            console.log(result);
            $("#linea_nuevo_titulo")[0].value = result.linea;
            var opciones_tutores = generar_opciones_tutores(result.tutores);
            document.getElementById("tutor_nuevo_titulo").innerHTML = "";
            for(var opcion of opciones_tutores){
                document.getElementById("tutor_nuevo_titulo").appendChild(opcion);
            }
       },
    })
}

function generar_opciones_tutores(tutores){
    var opciones_tutores = [];
    for(var tutor of tutores){
        var opcion = document.createElement("option");
        opcion.value = tutor[0];
        opcion.innerText = tutor[1]
        opciones_tutores.push(opcion);
    }
    // for(var i=0; i<=tutores.length; i++){
    //     var opcion = document.createElement("option");
    //     opc.value = tutores[i][0];
    //     option.innerText = tutores[i][1]
    //     opciones_tutores.push(opcion);
    // }
    return opciones_tutores;
}

function confirmar_borrado(event){
    //event.preventDefault();
    console.log("entro confirmar borrado");
    var destino = event.target.getAttribute("data-destino");
    console.log(destino); 
    var texto = event.target.getAttribute("data-texto");
    var confirmacion = confirm("Esta seguro que quiere borrar "+texto+"?")
    if(confirmacion) window.location = destino;
}

