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

      * `--samples <numero>`
    * **Descrição:** Define a qualidade da imagem gerada controlando a quantidade de "Samples" (Amostras) no motor de renderização Cycles do Blender. Valores menores são mais rápidos, valores maiores têm melhor resolução.
    * **Padrão:** `32` (Qualidade boa e rápida para e-commerce).
    * **Exemplo:** `python pipeline.py --samples 128` (Render de altíssima qualidade).

* `--time <segundos>`
    * **Descrição:** Impõe um limite de tempo estrito (em segundos) para a renderização de CADA câmera. Se você colocar 10, o Blender vai parar de renderizar em exatamente 10 segundos e aplicar a Inteligência Artificial (Denoiser) no que tiver conseguido calcular. Excelente para forçar produtividade máxima.
    * **Padrão:** `0` (Sem limite de tempo; o render só acaba quando atingir as Samples definidas).
    * **Exemplo:** `python pipeline.py --time 15` (Força o render de cada foto a durar no máximo 15s).

> 💡 **Dica de Produtividade:** Você pode combinar todas as flags para testes ultra-rápidos:
> `python pipeline.py --file meu_produto.stl --cor preto -ro --samples 16 --time 5`


* `--profile <nome_do_perfil>`
    * **Descrição:** Especifica exatamente qual perfil do PrusaSlicer (localizado na pasta `profiles/`) deve ser utilizado para gerar o fatiamento e a renderização. O script **não** rodará perfis múltiplos em lote; ele executará apenas o perfil informado.
    * **Padrão:** `020_standard`
    * **Exemplo:** `python pipeline.py --profile 012_fine`

* **🗂️ Projetos de Diagnóstico:**
    * Toda vez que o Blender finaliza um setup virtual, ele salva automaticamente uma cópia do projeto completo na pasta `blender_projects/`. Você pode abrir esse arquivo `.blend` manualmente para inspecionar escalas, materiais aplicados e posições de câmera caso algum render apresente anomalias.

    . Como fica o comando exato que você pediu

Para renderizar APENAS o teste.stl, com o perfil 020_standard, de forma direta (-ro), na cor preto, com boa qualidade e num limite rígido de 1 minuto:
Bash

python pipeline.py --file teste.stl --profile 020_standard --cor preto -ro --samples 64 --time 60

* `--material <nome_do_material>` (Substitui a antiga flag `--cor`)
    * **Descrição:** Puxa todas as configurações físicas (Cor Hexadecimal, Rugosidade, Reflexo Especular, Metálico) do arquivo `render_profiles.json`.
    * **Padrão:** `cinza`
    * **Exemplo:** `python pipeline.py --material petg_translucido`

* `--scale <fator_multiplicador>`
    * **Descrição:** A pipeline auto-escala os modelos para caberem numa Bounding Box virtual de 100mm, garantindo que objetos de qualquer tamanho fiquem em foco. Esta flag permite **sobrescrever** essa regra multiplicando o tamanho final. Um valor de `1.5` fará a peça parecer 50% maior (chegando mais perto da câmera). Um valor de `0.5` deixará ela 50% menor.
    * **Padrão:** `1.0`
    * **Exemplo:** `python pipeline.py --scale 1.5`

**⚙️ Configurações Avançadas (JSON):**
O projeto agora utiliza o arquivo `render_profiles.json` para separar a lógica dos dados de render. Nele você pode criar infinitos "materiais virtuais" ajustando a resposta à luz, além de configurar multiplicadores globais de iluminação da cena para todo o seu catálogo.

🚀 Exemplos Práticos de Uso (Copie e Cole)

Aqui estão os três fluxos de trabalho mais comuns para o dia a dia da pipeline:

1. O Retoque Rápido (Render Only)
Ideal para testar novas cores ou ajustes de luz em um arquivo que já foi fatiado e processado anteriormente. Ele ignora o PrusaSlicer e o conversor de malhas, indo direto para o Blender. Isso reduz um processo de minutos para apenas alguns segundos.
Bash

python pipeline.py --file case_orangepi.stl --profile 020_standard --material preto -ro

2. A Produção Completa (Do Zero ao Render)
O comando padrão e mais robusto. Ele pega um STL cru recém-saído do CAD, encontra a melhor face para impressão (auto-orientação), fatia no PrusaSlicer, constrói a malha 3D simulando o filamento e renderiza as 4 fotos no estúdio virtual com a qualidade máxima do perfil.
Bash

python pipeline.py --file suporte_drone.stl --profile 020_standard --material petg_translucido

3. O Modo "Fast & Furious" (Do Zero com Limites de Tempo e Qualidade)
Excelente para peças muito complexas ou testes rápidos onde você precisa ver o resultado final do G-code, mas não quer deixar a placa de vídeo travada. Ele processa o STL do zero, mas limita o motor do Blender a uma qualidade razoável (64 amostras) e corta o render de cada foto em no máximo 90 segundos, aplicando Inteligência Artificial (Denoiser) para limpar a imagem na marra.
Bash

python pipeline.py --file trava_scooter.stl --profile 012_fine --material cinza --samples 64 --time 90

pip install streamlit