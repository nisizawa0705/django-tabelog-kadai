function openTab(evt, tabName) {
    // すべてのタブコンテンツを非表示
    var tabContents = document.getElementsByClassName("tab-content");
    for (var i = 0; i < tabContents.length; i++) {
        tabContents[i].classList.remove("active");
    }

    // すべてのタブボタンのアクティブクラスを削除
    var tabButtons = document.getElementsByClassName("tab-button");
    for (var i = 0; i < tabButtons.length; i++) {
        tabButtons[i].classList.remove("active");
    }

    // クリックされたタブを表示し、アクティブクラスを追加
    document.getElementById(tabName).classList.add("active");
    evt.currentTarget.classList.add("active");
}
