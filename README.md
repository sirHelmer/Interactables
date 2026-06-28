# Interactables 🚀

Bem-vindo ao **Interactables**, um motor visual interativo e plataforma de apresentações construído inteiramente com Python e [Flet](https://flet.dev)! Este projeto nasceu como meu **Trabalho de Conclusão de Curso (TCC)** e evoluiu para uma ferramenta robusta e flexível para criar cenas dinâmicas, arrastar objetos, configurar propriedades em tempo real e até simular gravidade e colisões!

## 🎯 O que é o Interactables?

Sabe quando você precisa criar uma apresentação dinâmica ou prototipar um comportamento gráfico interativo, mas não quer lidar com motores de jogos pesados como Unity ou Unreal? 

O **Interactables** foi projetado para preencher essa lacuna. Ele permite que você:
- **Crie Projetos Visuais**: Interface Drag-and-Drop intuitiva direto no Canvas.
- **Hierarquia de Objetos**: Gerenciamento de z-index (trazer para frente/enviar para trás) em tempo real, igualzinho aos grandes softwares de design.
- **Painel de Propriedades**: Altere cores, tamanhos, bordas, posições e rotações de maneira dinâmica.
- **Física Integrada**: Adicione comportamentos (Behaviors) como *Mover Linear* ou *Gravidade* e assista a mágica acontecer!
- **Play & Pause Perfeitos**: Um modo apresentação em background sincronizado matematicamente a 60FPS usando a arquitetura nativa de PubSub do Flet, garantindo transições suaves e nenhum gargalo na interface principal.

## 🛠️ Tecnologias Utilizadas

- **Linguagem**: Python 3.10+
- **Framework UI**: Flet (Powered by Flutter) - Escolhido pela facilidade de criar interfaces modernas e nativas que rodam no Desktop, Web e Mobile.
- **Arquitetura**: Orientação a Objetos, Design Patterns, PubSub, e manipulação assíncrona.

## 📦 Funcionalidades Mágicas do Menu Arquivo

No decorrer do TCC, lapidamos a experiência de usuário (UX) focando em produtividade:
- **Salvar Como**: Duplica projetos de maneira limpa.
- **Exportação Nativa (.int)**: O projeto pode ser empacotado inteiro num arquivo zipado customizado com a extensão `.int`. Quer mandar pro colega? É só mandar esse arquivo. Quando ele abrir, o sistema descompacta magicamente onde ele quiser e já roda!
- **Auto Save Silencioso**: Uma Thread em background roda a cada um minuto salvando seu progresso silenciosamente (sem dar aquelas famosas travadinhas na tela).

## 🚀 Como Rodar Localmente

Certifique-se de ter o Python instalado e um ambiente virtual configurado.

1. Clone o repositório:
```bash
git clone https://github.com/SeuUsuario/Interactables.git
cd Interactables
```

2. Ative seu ambiente virtual (ex: `.venv_win`) e instale as dependências:
```bash
pip install -r requirements.txt
```
*(Caso não haja o requirements, um simples `pip install flet` geralmente basta!)*

3. Rode o app:
```bash
flet run App
```

### Para Compilar um Executável (.exe)
```bash
flet pack App/src/main.py --name "Interactables" --product-name "Interactables Studio" --product-version "1.0.0"
```

## ✨ Conclusão

Esse TCC foi uma jornada incrível de descobertas sobre como lidar com interfaces pesadas em Python, dominar o Flet e construir lógicas de física em tempo real. O resultado é um software redondinho, polido e pronto para expandir!

Gostou? Deixa uma ⭐ no repositório!
