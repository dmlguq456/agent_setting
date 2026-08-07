이 케이스는 static negative drill이다. OpenCode registered standard+
dispatch-depth-2 자체는 개통되었지만, 바인딩할 살아있는 depth-1 owner 행이 없는
요청은 runtime·registry row·prompt/log를 만들기 전에 exit 73과
`live-parent-not-found`로 차단되는지 검사한다.
