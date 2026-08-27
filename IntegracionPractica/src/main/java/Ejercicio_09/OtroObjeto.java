package Ejercicio_09;

public class OtroObjeto extends ObjetoDeArte {
    private String tipoEspecifico;

    public OtroObjeto(String id, String titulo, String desc, Integer anio, String pais, String cultura,
                      String epoca, Artista artista, EstadoTenencia estado, String tipoEspecifico) {
        super(id, titulo, desc, anio, pais, cultura, epoca, artista, estado);
        this.tipoEspecifico = tipoEspecifico;
    }
}
