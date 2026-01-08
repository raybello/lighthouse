
``` mermaid
graph TD
    const_a([ConstA<br/>CONST<br/>= 10])
    const_b([ConstB<br/>CONST<br/>= 4])
    const_c([ConstC<br/>CONST<br/>= 2])
    const_d([ConstD<br/>CONST<br/>= 4])
    add_1[Add1<br/>ADD<br/>= 14]
    mult_1{Multiply1<br/>MULTIPLY<br/>= 8}
    add_2[Add2<br/>ADD<br/>= 22]

    const_a --> add_1
    const_b --> add_1
    const_c --> mult_1
    const_d --> mult_1
    add_1 --> add_2
    mult_1 --> add_2

    %% Styling
    classDef constStyle fill:#3498db,stroke:#2980b9,stroke-width:2px,color:#fff
    classDef addStyle fill:#2ecc71,stroke:#27ae60,stroke-width:2px,color:#fff
    classDef multiplyStyle fill:#e74c3c,stroke:#c0392b,stroke-width:2px,color:#fff

    class const_a,const_b,const_c,const_d constStyle
    class add_1,add_2 addStyle
    class mult_1 multiplyStyle
```
