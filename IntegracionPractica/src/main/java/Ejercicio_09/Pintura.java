package Ejercicio_09;

public class Pintura extends ObjetoDeArte {
    private String tipoPintura; // Óleo, acuarela, etc.
    private String soporte;     // Lienzo, papel, etc.
    private String estilo;

    public Pintura(String id, String titulo, String desc, Integer anio, String pais, String cultura,
                   String epoca, Artista artista, EstadoTenencia estado,
                   String tipoPintura, String soporte, String estilo) {
        super(id, titulo, desc, anio, pais, cultura, epoca, artista, estado);
        this.tipoPintura = tipoPintura;
        this.soporte = soporte;
        this.estilo = estilo;
    }
}
