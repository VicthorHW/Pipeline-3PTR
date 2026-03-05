1. Escopo Técnico

Criar um script orquestrador em Python que sirva de ponte entre o fatiamento real (PrusaSlicer) e a fotografia virtual (Blender).
2. Parâmetros de Entrada (Input)

O programa deverá solicitar ao usuário:

    Arquivo: Seleção do STL original.

    Perfil: * P1: 0.20mm (Standard)

        P2: 0.12mm (Detail)

        P3: 0.20mm + Fuzzy Skin (Textured)

    Cor: * C1: Branco (Matte White)

        C2: Preto (Matte Black)

        C3: Cinza (Space Grey)

3. Lógica de Automação do Slicer (Stage 1)

    Processamento: O script executa o PrusaSlicer via CLI usando o perfil selecionado.

    Geração de Mesh: O G-code gerado é convertido em uma malha de "Toolpath" (mostrando as camadas reais e o efeito Fuzzy Skin).

    Nomenclatura: Os arquivos temporários seguem o padrão temp_output_[profile].obj.

4. Lógica de "Staging" no Blender (Stage 2)

    O Contentor (Bounding Box): O arquivo .blend mestre possui um volume invisível (ex: 150x150x150mm).

    Auto-Fit: O script de importação dentro do Blender deve:

        Calcular as dimensões do objeto importado.

        Redimensionar o objeto (Scale) para que ele preencha o máximo da "caixa" sem ultrapassá-la.

        Centralizar o objeto no eixo X e Y e encostar a base no eixo Z (chão).

    Câmeras Fixas: * Cam_Front: Visão frontal levemente superior.

        Cam_Perspective: Ângulo de 45 graus (Beleza).

        Cam_Top: Visão superior para detalhe de preenchimento.

        Cam_Macro: Foco em close-up para mostrar a textura da camada/Fuzzy Skin.

5. Lógica de Materiais e Render (Stage 3)

    Materiais Dinâmicos: O script atribui um material "Filamento" ao objeto importado. A cor desse material é alterada via código (RGB) com base na escolha inicial do usuário.

    Render Queue: O Blender renderiza as 4 câmeras em sequência.

    Otimização: * Engine: Cycles (GPU).

        Samples: 128 a 256.

        Denoise: OpenImageDenoise ativado.

        Saída: 1080x1080px.

        