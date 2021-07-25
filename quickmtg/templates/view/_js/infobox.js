$("#{{ id }}").dialog({
    autoOpen: false,
    modal: true,
    resizeable: false,
    draggable: false,
    width: "80%",
    height: $(window).height() - 100
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
    modal.dialog("open");
});