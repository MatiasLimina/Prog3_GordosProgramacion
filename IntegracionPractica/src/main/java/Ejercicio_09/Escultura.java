package Ejercicio_09;

public class Escultura extends ObjetoDeArte {
    private String material; // Mármol, bronce, etc.
    private double altura;
    private double peso;
    private String estilo;

    public Escultura(String id, String titulo, String desc, Integer anio, String pais, String cultura,
                     String epoca, Artista artista, EstadoTenencia estado,
                     String material, double altura, double peso, String estilo) {
        super(id, titulo, desc, anio, pais, cultura, epoca, artista, estado);
        this.material = material;
        this.altura = altura;
        this.peso = peso;
        this.estilo = estilo;
    }
}
