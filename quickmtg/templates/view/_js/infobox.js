var close_if_click_out = function(e) {
    $("#{{ id }}").dialog("close");
}
$("#{{ id }}").dialog({
    autoOpen: false,
    modal: true,
    resizable: false,
    draggable: false,
    open: function(e, ui) {
        var uiWidth = $(window).width() * 0.8;
        if (uiWidth > 800) {
            uiWidth = 800;
        }
        $("#{{ id }}").dialog("option", "width", uiWidth);
    },
    beforeClose: function(e, ui) {
        $("body").off("click", ".ui-widget-overlay", close_if_click_out);
    }
});
$("{{ opener_selector }}").click(function(e) {
    // get the data fields
    var data_source = $(this);
    if ("{{ opener_data_selector }}" !== "") {
        data_source = data_source.find("{{ opener_data_selector }}");
    }
    var cardName = data_source.data("name");
    var cardCount = data_source.data("owned");
    var cardFoil = "no";
    if (data_source.data("foil").toLowerCase() === 'true') {
        cardFoil = "yes";
    }
    var cardCond = data_source.data("cond");
    var cardImage = 'assets/images/' + data_source.data("img");

    // put data fields in the modal
    var modal = $("#{{ id }}");
    modal.find("[data-fill='name']").text(cardName);
    modal.find("[data-fill='owned']").text(cardCount);
    modal.find("[data-fill='foil']").text(cardFoil);
    modal.find("[data-fill='cond']").text(cardCond);
    modal.find("img[data-fill='image']").attr('src', cardImage);
    modal.dialog("option", "title", cardName);
    
    // finally, open it:
    $("body").on("click", ".ui-widget-overlay", close_if_click_out);
    modal.dialog("open");
});