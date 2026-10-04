document
.getElementById("searchInput")
.addEventListener(
    "keyup",
    function(){

        let value =
            this.value.toLowerCase();

        let rows =
            document.querySelectorAll(
                "#bookTable tbody tr"
            );

        rows.forEach(
            row => {

                row.style.display =
                    row.innerText
                        .toLowerCase()
                        .includes(value)
                    ? ""
                    : "none";
            }
        );
    }
);