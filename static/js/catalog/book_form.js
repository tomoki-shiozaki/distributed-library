document.addEventListener("DOMContentLoaded", function () {
    const isbnInput = document.getElementById("id_isbn");
    if (!isbnInput) return;

    isbnInput.addEventListener("blur", async function () {
        const isbn = isbnInput.value.trim();
        if (!isbn) return;

        try {
            const response = await fetch(`https://www.googleapis.com/books/v1/volumes?q=isbn:${isbn}`);
            const data = await response.json();

            if (!data.items || data.items.length === 0) {
                alert("本が見つかりませんでした。");
                return;
            }

            const info = data.items[0].volumeInfo;

            // 自動入力
            document.getElementById("id_title").value = info.title || "";
            document.getElementById("id_author").value = (info.authors || []).join(", ");
            document.getElementById("id_publisher").value = info.publisher || "";
            document.getElementById("id_published_date").value = info.publishedDate || "";
            document.getElementById("id_image_url").value = info.imageLinks?.thumbnail || "";

            const coverImg = document.getElementById("book-cover");
            if (info.imageLinks?.thumbnail) {
                coverImg.src = info.imageLinks.thumbnail;
                coverImg.style.display = "block";  // 表示
            } else {
                coverImg.src = "";
                coverImg.style.display = "none";  // 非表示
            }
        } catch (err) {
            console.error("APIエラー:", err);
            alert("本情報の取得に失敗しました。");
        }
    });
});
