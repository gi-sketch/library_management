document.addEventListener(
    "DOMContentLoaded",
    function(){

        const cards =
            document.querySelectorAll(
                ".feature-card"
            );

        cards.forEach(
            card => {

                card.addEventListener(
                    "mouseenter",
                    () => {
                        card.style.boxShadow =
                            "0 20px 40px rgba(0,0,0,.3)";
                    }
                );

                card.addEventListener(
                    "mouseleave",
                    () => {
                        card.style.boxShadow =
                            "none";
                    }
                );

            }
        );

    }
);