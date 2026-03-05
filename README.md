# Pipeline-3PTR
Criar um script orquestrador em Python que sirva de ponte entre o fatiamento real (PrusaSlicer) e a fotografia virtual (Blender).


Dependencies:

Para transformar essa ideia em realidade, vamos estruturar o projeto de forma profissional. Como você é estudante de Engenharia, vamos focar em um código modular: um Orquestrador (que manda) e um Conversor (que executa a matemática pesada).

Aqui está a organização lógica para começarmos agora:
1. Preparação do Ambiente (Virtual Environment)

Para evitar conflitos e garantir que as bibliotecas de processamento 3D funcionem bem, abra seu terminal na pasta do projeto e execute:
Bash

# Criar o ambiente virtual
python -m venv venv

# Ativar o ambiente (Windows)
.\venv\Scripts\activate

# Instalar as dependências necessárias
pip install numpy trimesh pygcode

numpy: Para cálculos matemáticos rápidos.

trimesh: Para gerar e exportar o arquivo STL de forma otimizada.

pygcode: Para interpretar as linhas de comando do G-code de forma precisa.



📋 Dependências e Requisitos

Para rodar a pipeline 3PTR (3D-Print-to-Render), você precisará dos seguintes softwares e bibliotecas instalados no seu ambiente:

Softwares:

    Python 3.x

    PrusaSlicer: Testado e homologado para a versão 2.9.4 (Via CLI).

    Blender 3.x ou superior (Para a etapa de renderização final - em desenvolvimento).

Bibliotecas Python:
Recomenda-se o uso de um ambiente virtual (venv). Instale as dependências com o comando:
Bash

pip install numpy trimesh

(Nota: A biblioteca pygcode foi removida em favor de um parser nativo usando RegEx para garantir maior performance e estabilidade).
🚀 Como Usar (CLI Flags)

O script pipeline.py é o orquestrador principal e pode ser controlado inteiramente via linha de comando.

Lista de Parâmetros (Flags):

    --file <nome_do_arquivo.stl>

        Descrição: Especifica qual arquivo STL será processado.

        Padrão: teste.stl (se omitido).

    -nr ou --no-rotation

        Descrição: Desativa completamente a auto-orientação inteligente (que busca a face mais plana). Usa a posição exata em que o STL foi exportado do seu software CAD.

    --rx <graus> | --ry <graus> | --rz <graus>

        Descrição: Aplica uma rotação manual específica (em graus) nos eixos X, Y ou Z antes do fatiamento. O uso de qualquer uma dessas flags desativa automaticamente a auto-orientação.

💡 Exemplos de Uso

1. Orientação Automática (Padrão):
Lê o arquivo teste.stl, encontra a face mais estável, encosta no chão virtual e gera as malhas.
Bash

python pipeline.py

2. Processar um arquivo específico (Auto-orientado):
Bash

python pipeline.py --file meu_produto.stl

3. Rotação Manual (Ex: Girar 90 graus no eixo X):
Ideal para peças onde a face plana estrutural não é o ângulo que você deseja mostrar na foto.
Bash

python pipeline.py --file meu_produto.stl --rx 90

4. Sem Rotação (No Rotation):
Mantém a orientação original do arquivo CAD, sem tentar estabilizar a peça e sem aplicar rotações extras.
Bash

python pipeline.py --file meu_produto.stl -nr



* `-ro` ou `--render-only`
    * **Descrição:** Modo "Apenas Render". Ignora as etapas de fatiamento no PrusaSlicer e conversão de malha. O script buscará diretamente o arquivo do toolpath já gerado na pasta `renders_mesh/` e o enviará para o Blender. Excelente para testar novas cores ou ajustes de luz no cenário de forma rápida.
    * **Exemplo de Uso:**
      ```bash
      python pipeline.py --file meu_produto.stl --cor branco --render-only
      ```