// CSRFトークンとゲームの初期データを読み込む。
// 初期データは、読み込み時のゲーム表示に使う。
const csrfToken = document.getElementById('csrf-data').dataset.csrf;

const initialMatchElement = document.getElementById('initial-match-data');
const matchId = initialMatchElement.dataset.matchId;
const initialTurn = initialMatchElement.dataset.initialTurn;
const initialBoard = JSON.parse(initialMatchElement.dataset.initialBoard);
const initialStatus = initialMatchElement.dataset.initialStatus;

// --- ターン管理: 表示と制御に関する処理 ---

//displayTurnIndicator()関数は、プレイヤーターン（黒か白）を表示する関数
//boardTurnは、'black\'s turn'か'white\'s turn'
const displayTurnIndicator = (boardTurn) => {
    const turnElement = document.getElementById('turn');
    if (boardTurn === 'black\'s turn') {
        turnElement.textContent = '黒'
    } else if (boardTurn === 'white\'s turn') {
        turnElement.textContent = '白'
    } else {
        turnElement.textContent = '不明'
    }
};

// 読み込み時に、ターンを表示する
displayTurnIndicator(initialTurn);

//パスボタンを押したときに、ターンを変更する関数
document.getElementById('pass-turn').addEventListener('click', async function (event) {
    try {
        const response = await fetch(`/match/local/${matchId}/pass-turn/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,  // CSRFトークンをヘッダーに追加
            },
            body: JSON.stringify({})
        });

        const data = await response.json();

        if (response.ok) {
            displayTurnIndicator(data.turn);
            console.log(`${data.message}`);
        } else {
            console.log(`Error: ${data.error}`);
        }
    } catch (error) {
        console.log(`Network error: ${error}`);
    }
});


// --- 盤面管理: 表示と駒を打つ処理 ---

// オセロの盤面を作る
// othelloGridContainerはオセロの盤面の枠組み
const othelloGridContainer = document.querySelector('.othello-grid-container');
for (let i = 0; i < 64; i++) {
    // othelloGridItemはオセロのマス目
    const othelloGridItem = document.createElement('div');
    othelloGridItem.classList.add('othello-grid-item');
    othelloGridItem.id = `othello-grid-item${i}`
    // othelloGridCellはオセロの駒
    const othelloGridCell = document.createElement('div');
    othelloGridCell.classList.add('othello-grid-cell');
    othelloGridCell.id = `othello-cell${i}`;
    // 駒othelloGridCellをマス目othelloGridItemに追加する
    othelloGridItem.appendChild(othelloGridCell);
    // マス目othelloGridItemを盤面othelloGridContainerに追加する
    othelloGridContainer.appendChild(othelloGridItem);
}

//モデルでは、オセロの盤面を表すboard---各セルをblack, white, emptyで管理する---は2次元配列
//一方、オセロの盤面をフロントエンド側で1次元配列で表した
// 2次元配列を1次元配列に変換するための関数
const flattenBoard = (board2D) => {
    const flatBoard = []
    for (let i = 0; i < 8; i++) {
        for (let j = 0; j < 8; j++) {
            flatBoard.push(board2D[i][j])
        }
    }
    return flatBoard
};

// 盤面を表示する関数
const displayBoard = (flatBoard) => {
    for (let i = 0; i < 64; i++) {
        const cell = document.getElementById(`othello-cell${i}`);
        if (flatBoard[i] === 'black') {
            cell.classList.add('black');
            cell.classList.remove('white', 'empty');
        } else if (flatBoard[i] === 'white') {
            cell.classList.add('white');
            cell.classList.remove('black', 'empty');
        }
    };
}

// （画面読み込み時の）初期状態の盤面を１次元化して、配列を取得する
const flatInitialBoard = flattenBoard(initialBoard);
// 画面読み込み時に盤面を表示する
displayBoard(flatInitialBoard);


// オセロの駒を打ったときにエラーが生じたら、メッセージを表示する
const responseDiv = document.getElementById('response');
//クリックして、オセロの駒を打つ処理
for (let i = 0; i < 64; i++) {
    document.getElementById(`othello-grid-item${i}`).addEventListener('click', async function (event) {
        try {
            const response = await fetch(`/match/local/${matchId}/place-piece/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,  // CSRFトークンをヘッダーに追加
                },
                body: JSON.stringify({ cell: i})
            });

            const data = await response.json();

            if (response.ok) {
                // 更新された盤面を一次元化する
                flatUpdatedBoard = flattenBoard(data.board);
                // 盤面の表示を更新する
                displayBoard(flatUpdatedBoard);
                // ターンの表示を更新する
                displayTurnIndicator(data.turn);
            }
            else {
                responseDiv.innerHTML = `<p>Error: ${data.error}</p>`;
            }
        } catch (error) {
            responseDiv.innerHTML = `<p>Network error: ${error}</p>`;
        }
    });
};



// --- ゲーム結果管理: 終局処理とゲーム結果表示 ---

// ゲーム結果を表示する関数
// 引数は辞書で、result = { "blackCount": black_count, "whiteCount": white_count, "winner": winner, }
const displayGameResult = (result) => {
    const countResult = document.querySelector("#result-box .counts");
    const gameResult = document.querySelector("#result-box .result");
    countResult.innerHTML = `黒${result["blackCount"]}枚、白${result["whiteCount"]}枚。`
    if (result["winner"] === "black") {
        gameResult.innerHTML = `黒の勝ちです。`
    } else if (result["winner"] === "white") {
        gameResult.innerHTML = `白の勝ちです。`
    } else {
        gameResult.innerHTML = `引き分けです。`
    }
};

// ゲーム結果を取得し、取得した結果を表示する非同期関数
const fetchGameResult = async () => {
    try {
        const response = await fetch(`/match/local/${matchId}/end-game/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,  // CSRFトークンをヘッダーに追加
            },
            body: JSON.stringify({})
        });

        const data = await response.json();

        if (response.ok) {
            displayGameResult(data);
        } else {
            console.log(`Error: ${data.error}`);
        }
    } catch (error) {
        console.log(`Network error: ${error}`);
    }
};

// ページ読み込み時に対局が終了していたら、結果を表示する
if (initialStatus !== "対局中") {
    window.addEventListener("DOMContentLoaded", fetchGameResult);
}

// 終局ボタンを押したら、終局処理を行う
document.getElementById('end-game').addEventListener('click', async function () {
    const answer = confirm("本当にゲームを終了しますか？OKとすると、黒白それぞれの枚数を数えて、勝敗を決定します。");
    if (answer) {
        fetchGameResult()
    }
});
